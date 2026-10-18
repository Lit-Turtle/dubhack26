import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from train_food30 import INGREDIENTS, select_labels, prepare, boost_multi, export_demo_combos
import yaml, json

class Food30Tests(unittest.TestCase):
    def test_remapping_preserves_boxes(self):
        self.assertEqual(select_labels('8 0.5 0.4 0.3 0.2\n9 0.1 0.2 0.3 0.4', {8:2,9:None}), ['2 0.5 0.4 0.3 0.2'])
    def test_invalid_annotations_fail(self):
        for row in ['0 0.5 0.5 0 0.2', '0 nan 0.5 0.2 0.2', '0 1.2 0.5 0.2 0.2', '0 0.5']:
            with self.subTest(row=row), self.assertRaises(ValueError):select_labels(row,{0:0})
    def test_split_duplicates_removed_and_ids_remapped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source';root.mkdir(); names=dict(enumerate(reversed(INGREDIENTS)))
            for split in ['train','val','test']:
                (root/'images'/split).mkdir(parents=True);(root/'labels'/split).mkdir(parents=True)
                (root/'images'/split/'all.jpg').write_bytes(split.encode())
                (root/'labels'/split/'all.txt').write_text('\n'.join(f'{i} 0.5 0.5 0.2 0.2' for i in range(30)))
            (root/'images/train/leak.jpg').write_bytes(b'test')
            (root/'labels/train/leak.txt').write_text('0 0.5 0.5 0.2 0.2')
            source=root/'dataset.yaml';source.write_text(yaml.safe_dump({'path':str(root),'names':names,**{s:f'images/{s}' for s in ['train','val','test']}}))
            out=Path(tmp)/'food30';prepare(source,out)
            report=json.loads((out/'preparation-report.json').read_text())
            self.assertEqual(report['splits']['train']['excluded']['duplicate_in_another_split'],1)
            self.assertEqual(report['splits']['train']['images'],1)
            hashes=[{p.stem for p in (out/'images'/s).iterdir()} for s in ['train','val','test']]
            self.assertFalse(hashes[0]&hashes[1] or hashes[0]&hashes[2] or hashes[1]&hashes[2])
            self.assertEqual(yaml.safe_load((out/'dataset.yaml').read_text())['names'][0],'onion')

    def test_boost_multi_repeats_combo_photos_only_in_train(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)/'food30'
            for split in ['train','val','test']:
                (src/'images'/split).mkdir(parents=True)
                (src/'labels'/split).mkdir(parents=True)
                (src/'images'/split/'single.jpg').write_bytes(f'{split}-single'.encode())
                (src/'labels'/split/'single.txt').write_text('0 0.5 0.5 0.2 0.2\n')
                (src/'images'/split/'combo.jpg').write_bytes(f'{split}-combo'.encode())
                (src/'labels'/split/'combo.txt').write_text('\n'.join(f'{i} 0.{i+1} 0.5 0.2 0.2' for i in range(30)))
            (src/'dataset.yaml').write_text(yaml.safe_dump({
                'path': str(src), 'train':'images/train','val':'images/val','test':'images/test',
                'names': dict(enumerate(INGREDIENTS)),
            }))
            out = Path(tmp)/'food30-multi'
            boost_multi(src, out, extra_copies=3)
            train_stems = {p.stem for p in (out/'images'/'train').iterdir()}
            self.assertEqual(train_stems, {'single', 'combo', 'combo-multi1', 'combo-multi2'})
            self.assertEqual({p.stem for p in (out/'images'/'val').iterdir()}, {'single', 'combo'})
            report = json.loads((out/'preparation-report.json').read_text())
            self.assertEqual(report['splits']['train']['multi_ingredient_images'], 1)
            self.assertEqual(report['splits']['train']['images'], 4)

    def test_export_demo_prefers_two_to_five_ingredients(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)/'food30'
            (src/'images'/'test').mkdir(parents=True)
            (src/'labels'/'test').mkdir(parents=True)
            (src/'images'/'val').mkdir(parents=True)
            (src/'labels'/'val').mkdir(parents=True)
            for index in range(12):
                names = [0, 1] if index < 6 else [0, 6, 16]
                (src/'images'/'test'/f'{index}.jpg').write_bytes(f'img{index}'.encode())
                (src/'labels'/'test'/f'{index}.txt').write_text('\n'.join(f'{i} 0.5 0.5 0.2 0.2' for i in names))
            dest = Path(tmp)/'demo'
            manifest = export_demo_combos(src, dest, count=10)
            self.assertEqual(len(manifest), 10)
            self.assertTrue((dest/'manifest.json').is_file())
            self.assertTrue({tuple(item['ingredients']) for item in manifest} >= {('onion', 'tomato'), ('onion', 'lettuce', 'chicken')})

if __name__=='__main__':unittest.main()
