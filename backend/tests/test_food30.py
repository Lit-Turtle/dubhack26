import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from train_food30 import INGREDIENTS, select_labels, prepare
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

if __name__=='__main__':unittest.main()
