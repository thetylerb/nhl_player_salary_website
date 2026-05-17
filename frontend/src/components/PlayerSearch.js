import React, { useState, useEffect, useRef, useCallback } from 'react';
import { searchPlayers } from '../services/api';

function useDebounce(value, delay) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

function initials(name) {
  if (!name) return '??';
  return name.split(' ').map((p) => p[0]).join('').slice(0, 2).toUpperCase();
}

function fmtSalary(n) {
  if (!n) return null;
  return `$${(n / 1_000_000).toFixed(2)}M`;
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

  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const showDropdown = open && (loading || results.length > 0 || (debouncedQuery.length >= 2 && !loading));

  // First result vs the rest
  const first = results[0];
  const rest = results.slice(1);

  return (
    <section className="search-wrap" ref={containerRef}>
      <div className="search-box">
        <div className="search-row">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
            <circle cx="11" cy="11" r="7"/>
            <path d="M21 21l-4-4"/>
          </svg>
          <input
            type="text"
            placeholder="Search any NHL player — by name, team, or position"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => results.length > 0 && setOpen(true)}
            onKeyDown={handleKeyDown}
            autoComplete="off"
          />
          <span className="search-kbd">⌘ K</span>
        </div>
      </div>

      {showDropdown && (
        <div className="dropdown">
          {loading && (
            <div className="dd-loading">Searching players…</div>
          )}
          {!loading && results.length === 0 && debouncedQuery.length >= 2 && (
            <div className="dd-empty">No players found for "{debouncedQuery}"</div>
          )}
          {!loading && first && (
            <>
              <div className="dd-label">Top match</div>
              <div
                className={`dd-item${highlightedIndex === 0 ? ' active' : ''}`}
                onMouseEnter={() => setHighlightedIndex(0)}
                onClick={() => handleSelect(first)}
              >
                <div className="dd-head">{initials(first.name)}</div>
                <div className="dd-name-wrap">
                  <span className="dd-name">{first.name}</span>
                  <span className="dd-meta">
                    {first.team && <>{first.team}<span>·</span></>}
                    {first.position && <>{first.position}</>}
                  </span>
                </div>
                <span className="dd-pos">{first.position || '—'}</span>
                {fmtSalary(first.salary?.aav) && (
                  <span className="dd-salary">{fmtSalary(first.salary?.aav)}</span>
                )}
              </div>
            </>
          )}
          {!loading && rest.length > 0 && (
            <>
              <div className="dd-label">Other players</div>
              {rest.map((player, i) => {
                const idx = i + 1;
                return (
                  <div
                    key={player.nhl_id || idx}
                    className={`dd-item${highlightedIndex === idx ? ' active' : ''}`}
                    onMouseEnter={() => setHighlightedIndex(idx)}
                    onClick={() => handleSelect(player)}
                  >
                    <div className="dd-head">{initials(player.name)}</div>
                    <div className="dd-name-wrap">
                      <span className="dd-name">{player.name}</span>
                      <span className="dd-meta">
                        {player.team && <>{player.team}<span>·</span></>}
                        {player.position && <>{player.position}</>}
                      </span>
                    </div>
                    <span className="dd-pos">{player.position || '—'}</span>
                    {fmtSalary(player.salary?.aav) && (
                      <span className="dd-salary">{fmtSalary(player.salary?.aav)}</span>
                    )}
                  </div>
                );
              })}
            </>
          )}
        </div>
      )}
    </section>
  );
}
