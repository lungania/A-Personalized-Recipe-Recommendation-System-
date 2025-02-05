import React, { useState, useEffect, useCallback } from 'react';

return (
  <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
    <h1>Recipe Recommendation System</h1>
    <p>If you see this, React is working!</p>
  </div>
);

// Debounce hook
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Loading spinner component (consider using a real spinner library or custom CSS)
const Spinner = () => <p>Loading...</p>;

// Error display component
const ErrorDisplay = ({ message }) => (
  <p style={{ color: 'red' }}>{message}</p>
);

// Recommendations list component
const RecommendationsList = ({ recommendations }) => (
  <>
    <h2>Recommendations:</h2>
    {recommendations.length > 0 ? (
      <ul>
        {recommendations.map((item, index) => (
          <li key={index} style={{ marginBottom: '10px' }}>
            <h3>{item.name}</h3>
            <p>Similarity: {item.similarity.toFixed(2)}</p>
            <p>{item.description}</p>
          </li>
        ))}
      </ul>
    ) : (
      <p>No recommendations available.</p>
    )}
  </>
);

function App() {
  const [preferences, setPreferences] = useState('');
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const debouncedPreferences = useDebounce(preferences, 300);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://127.0.0.1:5000/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ preferences: debouncedPreferences }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch recommendations');
      }

      const data = await response.json();
      setRecommendations(data.recommendations);
    } catch (error) {
      setError('Error fetching recommendations. Please try again later.');
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
    }
  }, [debouncedPreferences]);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Recipe Recommendation System</h1>
      <form onSubmit={handleSubmit} style={{ marginBottom: '20px' }}>
        <label>
          Enter your preferences:
          <input
            type="text"
            value={preferences}
            onChange={(e) => setPreferences(e.target.value)}
            style={{ marginLeft: '10px', padding: '5px', width: '300px' }}
          />
        </label>
        <button type="submit" style={{ marginLeft: '10px', padding: '5px 10px' }}>
          Get Recommendations
        </button>
      </form>
      <div>
        {loading ? <Spinner /> : error ? <ErrorDisplay message={error} /> : <RecommendationsList recommendations={recommendations} />}
      </div>
    </div>
  );
}

console.log('Rendering RecommendationsList:', recommendations);
return <RecommendationsList recommendations={recommendations} />;

export default App;