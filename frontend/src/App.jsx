import React, { useState } from 'react';
import { detectIngredients, getRecipes } from './api';
import Flipbook from './Flipbook';

const DIETS = [
  { id: 'vegetarian', label: 'Vegetarian' },
  { id: 'vegan', label: 'Vegan' },
  { id: 'pescatarian', label: 'Pescatarian' },
  { id: 'halal', label: 'Halal' },
  { id: 'kosher', label: 'Kosher' },
];

const ALLERGIES = [
  { id: 'peanuts', label: 'Peanuts' },
  { id: 'tree nuts', label: 'Tree nuts' },
  { id: 'dairy', label: 'Dairy' },
  { id: 'lactose', label: 'Lactose' },
  { id: 'gluten', label: 'Gluten' },
  { id: 'eggs', label: 'Eggs' },
  { id: 'soy', label: 'Soy' },
  { id: 'fish', label: 'Fish' },
  { id: 'shellfish', label: 'Shellfish' },
  { id: 'sesame', label: 'Sesame' },
];

const GOALS = [
  { id: 'high-protein', label: 'High-protein' },
  { id: 'low-carb', label: 'Low-carb' },
  { id: 'keto', label: 'Keto' },
  { id: 'low-sodium', label: 'Low-sodium' },
  { id: 'low-sugar', label: 'Low-sugar' },
  { id: 'low-fat', label: 'Low-fat' },
  { id: 'calorie-conscious', label: 'Calorie-conscious' },
];

const OTHER = [
  { id: 'dairy free', label: 'Dairy free' },
  { id: 'gluten free', label: 'Gluten free' },
  { id: 'paleo', label: 'Paleo' },
];

function toggleValue(values, value) {
  return values.includes(value) ? values.filter(item => item !== value) : [...values, value];
}

function ChipGroup({ title, hint, options, selected, onToggle, multiple = true }) {
  return (
    <fieldset className="pref-group">
      <legend>{title}</legend>
      {hint ? <p className="pref-hint">{hint}</p> : null}
      <div className="chips">
        {options.map(option => {
          const on = multiple ? selected.includes(option.id) : selected === option.id;
          return (
            <button type="button" key={option.id} className={on ? 'chip on' : 'chip'} aria-pressed={on} onClick={() => onToggle(option.id)}>
              {option.label}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}

export default function App() {
  const [ingredients, setIngredients] = useState(['rice', 'carrot']);
  const [draft, setDraft] = useState('');
  const [minutes, setMinutes] = useState(30);
  const [servings, setServings] = useState(2);
  const [diet, setDiet] = useState('');
  const [allergies, setAllergies] = useState([]);
  const [goals, setGoals] = useState([]);
  const [other, setOther] = useState([]);
  const [customPref, setCustomPref] = useState('');
  const [recipes, setRecipes] = useState([]);
  const [selected, setSelected] = useState(null);
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  function addIngredient(event) {
    event.preventDefault();
    const name = draft.trim().toLowerCase();
    if (name) setIngredients(previous => [...new Set([...previous, name])]);
    setDraft('');
    setRecipes([]);
  }

  async function upload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true); setNotice('');
    try {
      const result = await detectIngredients(file);
      setIngredients(previous => [...new Set([...previous, ...result.detections.map(item => item.label)])]);
      setRecipes([]);
      setNotice(result.message);
    } catch (error) { setNotice(error.message); }
    finally { setBusy(false); event.target.value = ''; }
  }

  function addCustomPref(event) {
    event.preventDefault();
    const value = customPref.trim().toLowerCase();
    if (!value || other.length >= 20) return;
    setOther(previous => [...new Set([...previous, value])]);
    setCustomPref('');
    setRecipes([]);
  }

  async function generate(event) {
    event.preventDefault();
    setBusy(true); setNotice(''); setRecipes([]);
    try {
      const result = await getRecipes({
        ingredients,
        max_minutes: Number(minutes),
        servings: Number(servings),
        diet,
        allergies,
        nutrition_goals: goals,
        other_preferences: other,
        vegetarian: diet === 'vegetarian' || diet === 'vegan',
      });
      setRecipes(result.recipes);
      setSelected(null);
      setNotice(result.message);
    } catch (error) { setNotice(error.message); }
    finally { setBusy(false); }
  }

  if (selected) return <Flipbook recipe={selected} onBack={() => setSelected(null)} />;

  return <main>
    <header><p className="eyebrow">PIC A DISH</p><h1>Your ingredients. Tonight’s dinner.</h1><p>Confirm your pantry and find meals.</p></header>
    <section><h2>1. Your pantry</h2><p>Upload a pantry photo, or add ingredients manually.</p>
      <label>Ingredient photo<input type="file" accept="image/jpeg,image/png,image/webp" onChange={upload} disabled={busy} /></label>
      <ul className="pantry">{ingredients.map((ingredient, index) => <li key={index}>
        <input aria-label={`Ingredient ${index + 1}`} value={ingredient} disabled={busy} maxLength={80} onChange={event => { setIngredients(items => items.map((item, i) => i === index ? event.target.value : item)); setRecipes([]); }} />
        <button type="button" disabled={busy} aria-label={`Remove ${ingredient}`} onClick={() => { setIngredients(items => items.filter((_, i) => i !== index)); setRecipes([]); }}>Remove</button>
      </li>)}</ul>
      <form onSubmit={addIngredient} className="inline"><input aria-label="New ingredient" placeholder="Add an ingredient" value={draft} maxLength={80} onChange={event => setDraft(event.target.value)} disabled={busy} /><button disabled={busy || !draft.trim() || ingredients.length >= 50}>Add</button></form>
    </section>
    <section><h2>2. Meal preferences</h2><form onSubmit={generate}>
      <div className="basics"><label>Max cooking time (minutes)<input type="number" min="5" max="180" required value={minutes} onChange={event => setMinutes(event.target.value)} /></label>
      <label>Servings<input type="number" min="1" max="12" required value={servings} onChange={event => setServings(event.target.value)} /></label></div>
      <ChipGroup title="Diet type" hint="Pick one, or leave unset." options={[{ id: '', label: 'Any' }, ...DIETS]} selected={diet} multiple={false} onToggle={value => { setDiet(value); setRecipes([]); }} />
      <ChipGroup title="Allergies and intolerances" hint="Select all that apply." options={ALLERGIES} selected={allergies} onToggle={value => { setAllergies(items => toggleValue(items, value)); setRecipes([]); }} />
      <ChipGroup title="Nutrition goals" hint="Optional targets for the recipes." options={GOALS} selected={goals} onToggle={value => { setGoals(items => toggleValue(items, value)); setRecipes([]); }} />
      <ChipGroup title="Other preferences" hint="Pick a preset or type your own." options={OTHER} selected={other} onToggle={value => { setOther(items => toggleValue(items, value)); setRecipes([]); }} />
      {other.filter(value => !OTHER.some(option => option.id === value)).length ? (
        <div className="chips custom-chips">
          {other.filter(value => !OTHER.some(option => option.id === value)).map(value => (
            <button type="button" key={value} className="chip on" aria-label={`Remove ${value}`} onClick={() => { setOther(items => items.filter(item => item !== value)); setRecipes([]); }}>
              {value} ×
            </button>
          ))}
        </div>
      ) : null}
      <div className="inline pref-add">
        <input
          aria-label="Custom preference"
          placeholder="Type a specific preference"
          value={customPref}
          maxLength={80}
          disabled={busy}
          onChange={event => setCustomPref(event.target.value)}
          onKeyDown={event => { if (event.key === 'Enter') addCustomPref(event); }}
        />
        <button type="button" disabled={busy || !customPref.trim() || other.length >= 20} onClick={addCustomPref}>Add</button>
      </div>
      <button className="find-recipes" disabled={busy || !ingredients.some(item => item.trim())}>{busy ? 'Working…' : 'Find recipes'}</button>
    </form></section>
    <p role="status">{notice}</p>
    <div className="recipes">{recipes.map(recipe => <article key={recipe.name}><h2>{recipe.name}</h2><p>{recipe.estimated_minutes} minutes · {recipe.servings} servings</p>
      <h3>Shopping list</h3>
      {recipe.missing_ingredients.length
        ? <ul className="shopping-list">{recipe.missing_ingredients.map(item => <li key={item}>{item}</li>)}</ul>
        : <p className="shopping-empty">Nothing extra!</p>}
      <button type="button" className="select-recipe" onClick={() => setSelected(recipe)}>Select</button>
    </article>)}</div>
    <footer>Diet and allergy filters are a starting point, not medical or allergy advice.</footer>
  </main>;
}
