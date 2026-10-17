import React, { useState } from 'react';
import { detectIngredients, getRecipes } from './api';

export default function App() {
  const [ingredients, setIngredients] = useState(['rice', 'egg', 'carrot', 'broccoli']);
  const [draft, setDraft] = useState('');
  const [minutes, setMinutes] = useState(30);
  const [servings, setServings] = useState(2);
  const [vegetarian, setVegetarian] = useState(false);
  const [exclusions, setExclusions] = useState('');
  const [recipes, setRecipes] = useState([]);
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

  async function generate(event) {
    event.preventDefault();
    setBusy(true); setNotice(''); setRecipes([]);
    try {
      const result = await getRecipes({
        ingredients, max_minutes: Number(minutes), servings: Number(servings), vegetarian,
        exclusions: exclusions.split(',').map(value => value.trim().toLowerCase()).filter(Boolean),
      });
      setRecipes(result.recipes);
      setNotice(result.message);
    } catch (error) { setNotice(error.message); }
    finally { setBusy(false); }
  }

  return <main>
    <header><p className="eyebrow">PANTRYPLAY · STARTER</p><h1>Your ingredients. Tonight’s dinner.</h1><p>Confirm your pantry and find meals with less extra shopping.</p></header>
    <section><h2>1. Your pantry</h2><p>Upload a pantry photo for YOLO object detection, or add ingredients manually.</p>
      <label>Ingredient photo<input type="file" accept="image/jpeg,image/png,image/webp" onChange={upload} disabled={busy} /></label>
      <ul className="pantry">{ingredients.map((ingredient, index) => <li key={index}>
        <input aria-label={`Ingredient ${index + 1}`} value={ingredient} disabled={busy} maxLength={80} onChange={event => { setIngredients(items => items.map((item, i) => i === index ? event.target.value : item)); setRecipes([]); }} />
        <button type="button" disabled={busy} aria-label={`Remove ${ingredient}`} onClick={() => { setIngredients(items => items.filter((_, i) => i !== index)); setRecipes([]); }}>Remove</button>
      </li>)}</ul>
      <form onSubmit={addIngredient} className="inline"><input aria-label="New ingredient" placeholder="Add an ingredient" value={draft} maxLength={80} onChange={event => setDraft(event.target.value)} disabled={busy} /><button disabled={busy || !draft.trim() || ingredients.length >= 50}>Add</button></form>
    </section>
    <section><h2>2. Meal preferences</h2><form onSubmit={generate}>
      <div className="preferences"><label>Max cooking time (minutes)<input type="number" min="5" max="180" required value={minutes} onChange={event => setMinutes(event.target.value)} /></label>
      <label>Servings<input type="number" min="1" max="12" required value={servings} onChange={event => setServings(event.target.value)} /></label>
      <label>Excluded ingredients (comma separated)<input value={exclusions} onChange={event => setExclusions(event.target.value)} placeholder="egg, broccoli" /></label></div>
      <label className="checkbox"><input type="checkbox" checked={vegetarian} onChange={event => setVegetarian(event.target.checked)} /> Vegetarian</label>
      <button disabled={busy || !ingredients.some(item => item.trim())}>{busy ? 'Working…' : 'Find recipes'}</button>
    </form></section>
    <p role="status">{notice}</p>
    <div className="recipes">{recipes.map(recipe => <article key={recipe.name}><h2>{recipe.name}</h2><p>{recipe.estimated_minutes} minutes · {recipe.servings} servings</p>
      <p><strong>You have:</strong> {recipe.ingredients_used.join(', ') || 'None'}</p>
      <p><strong>Shopping list:</strong> {recipe.missing_ingredients.join(', ') || 'Nothing extra!'}</p>
      <details><summary>Ingredients and instructions</summary><ul>{recipe.ingredients.map(item => <li key={item.name}>{item.quantity} {item.unit} {item.name}</li>)}</ul><ol>{recipe.steps.map(step => <li key={step}>{step}</li>)}</ol></details>
    </article>)}</div>
    <footer>Starter recipes use exact ingredient names. Exclusions are a basic filter, not an allergy checker.</footer>
  </main>;
}
