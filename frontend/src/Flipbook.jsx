import React, { useEffect, useState } from 'react';

export default function Flipbook({ recipe, onBack }) {
  const steps = recipe.steps ?? [];
  const lastIndex = steps.length;
  const [index, setIndex] = useState(0);
  const [flip, setFlip] = useState('');
  const done = index === lastIndex;
  const flipping = Boolean(flip);

  function go(delta) {
    const next = index + delta;
    if (flipping || next < 0 || next > lastIndex) return;
    setFlip(delta > 0 ? 'next' : 'prev');
    window.setTimeout(() => {
      setIndex(next);
      setFlip('');
    }, 420);
  }

  useEffect(() => {
    function onKey(event) {
      if (event.key === 'ArrowRight') go(1);
      if (event.key === 'ArrowLeft') go(-1);
      if (event.key === 'Escape') onBack();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  return (
    <main className="flipbook-page">
      <button type="button" className="flipbook-back" onClick={onBack}>← Back</button>
      <p className="eyebrow">BUILD GUIDE</p>
      <h1>{recipe.name}</h1>
      <p className="flipbook-meta">{recipe.estimated_minutes} minutes · {recipe.servings} servings</p>

      <div className="flipbook">
        <button type="button" className="flip-arrow" disabled={index === 0 || flipping} onClick={() => go(-1)} aria-label="Previous step">◀</button>
        <div className={`lego-book${flip ? ` flip-${flip}` : ''}`}>
          <div className="lego-studs" aria-hidden="true">
            {Array.from({ length: 3 }, (_, stud) => <span key={stud} className="stud" />)}
          </div>
          {done ? (
            <>
              <p className="step-badge">Complete</p>
              <p className="step-text">You made {recipe.name}. Nice build.</p>
              <button type="button" className="done-brick" onClick={onBack}>Back to recipes</button>
            </>
          ) : (
            <>
              <p className="step-badge">Step {index + 1} / {steps.length || 1}</p>
              <p className="step-text">{steps[index] || 'No steps were provided for this recipe.'}</p>
            </>
          )}
        </div>
        <button type="button" className="flip-arrow" disabled={done || flipping || !steps.length} onClick={() => go(1)} aria-label="Next step">▶</button>
      </div>

      <div className="step-dots">
        {steps.map((_, step) => (
          <button
            key={step}
            type="button"
            className={`dot${step === index ? ' active' : ''}`}
            disabled={flipping}
            aria-label={`Go to step ${step + 1}`}
            onClick={() => setIndex(step)}
          />
        ))}
      </div>
    </main>
  );
}
