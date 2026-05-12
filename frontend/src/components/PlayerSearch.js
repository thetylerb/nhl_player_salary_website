import React, { useState, useEffect, useRef, useCallback } from 'react';
import './PlayerSearch.css';
import { searchPlayers } from '../services/api';

function useDebounce(value, delay) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

export default function PlayerSearch({ onPlayerSelect }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const debouncedQuery = useDebounce(query, 280);
  const containerRef = useRef(null);

  useEffect(() => {
    if (debouncedQuery.length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }
    setLoading(true);
    searchPlayers(debouncedQuery)
      .then((players) => {
        setResults(players);
        setOpen(true);
        setHighlightedIndex(players.length > 0 ? 0 : -1);
      })
      .catch(() => setResults([]))
      .finally(() => setLoading(false));
  }, [debouncedQuery]);

  const handleSelect = useCallback((player) => {
    setQuery(player.name);
    setOpen(false);
    setResults([]);
    onPlayerSelect(player);
  }, [onPlayerSelect]);

  const handleClear = () => {
    setQuery('');
    setResults([]);
    setOpen(false);
    setHighlightedIndex(-1);
  };

  const handleKeyDown = useCallback((e) => {
    if (!open || results.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightedIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const target = results[highlightedIndex >= 0 ? highlightedIndex : 0];
      if (target) handleSelect(target);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  }, [open, results, highlightedIndex, handleSelect]);

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div className="search-container" ref={containerRef}>
      <label className="search-label" htmlFor="player-search">Search NHL Player</label>
      <div className="search-input-wrapper">
        <span className="search-icon">🔍</span>
        <input
          id="player-search"
          className="search-input"
          type="text"
          placeholder="e.g. Connor McDavid, Nathan MacKinnon..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
          onKeyDown={handleKeyDown}
          autoComplete="off"
        />
        {query && (
          <button className="clear-btn" onClick={handleClear} aria-label="Clear search">✕</button>
        )}
      </div>

      {open && (
        <div className="search-dropdown">
          {loading && (
            <div className="search-loading">
              <span className="search-loading-dot" />
              Searching players...
            </div>
          )}
          {!loading && results.length === 0 && (
            <div className="no-results">No players found for "{query}"</div>
          )}
          {!loading && results.map((player, i) => (
            <div
              key={player.nhl_id || i}
              className={`search-result${i === highlightedIndex ? ' highlighted' : ''}`}
              onMouseEnter={() => setHighlightedIndex(i)}
              onClick={() => handleSelect(player)}
            >
              <div>
                <div className="result-name">{player.name}</div>
                <div className="result-meta">
                  {player.team && <span className="result-team">{player.team}</span>}
                  {player.position && <span className="result-position">{player.position}</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
