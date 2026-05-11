"""
Static seed dataset (~100 NHL players) with 2023-24 season stats and contract AAV.
Stats are approximate but realistic. Used as fallback when external APIs are unavailable.
"""

# Each entry: player_id (NHL API), name, team, position, age, experience,
#   fa_type (RFA/UFA), aav ($), contract_years, expiry_season,
#   and stats dict with keys matching the comparables engine.

SEED_PLAYERS = [
    # ─── ELITE CENTERS ───────────────────────────────────────────────────────
    {
        "player_id": "8478483", "name": "Connor McDavid", "team": "EDM",
        "position": "C", "age": 27, "experience": 9, "fa_type": "UFA",
        "aav": 12500000, "contract_years": 8, "expiry_season": 2026,
        "stats": {
            "games_played": 75, "goals": 32, "assists": 68, "points": 100,
            "plus_minus": 22, "toi_per_game": 21.5,
            "goals_per_60": 2.7, "assists_per_60": 5.7, "points_per_60": 8.4,
            "corsi_for_pct": 55.2, "xgf_pct": 56.0, "penalty_diff_per_60": 0.2,
        },
    },
    {
        "player_id": "8477492", "name": "Nathan MacKinnon", "team": "COL",
        "position": "C", "age": 28, "experience": 11, "fa_type": "UFA",
        "aav": 12600000, "contract_years": 7, "expiry_season": 2025,
        "stats": {
            "games_played": 82, "goals": 51, "assists": 89, "points": 140,
            "plus_minus": 26, "toi_per_game": 22.0,
            "goals_per_60": 3.7, "assists_per_60": 6.4, "points_per_60": 10.1,
            "corsi_for_pct": 56.1, "xgf_pct": 57.2, "penalty_diff_per_60": 0.1,
        },
    },
    {
        "player_id": "8478402", "name": "Auston Matthews", "team": "TOR",
        "position": "C", "age": 26, "experience": 8, "fa_type": "UFA",
        "aav": 13250000, "contract_years": 4, "expiry_season": 2028,
        "stats": {
            "games_played": 81, "goals": 69, "assists": 54, "points": 123,
            "plus_minus": 15, "toi_per_game": 20.5,
            "goals_per_60": 5.3, "assists_per_60": 4.1, "points_per_60": 9.4,
            "corsi_for_pct": 54.0, "xgf_pct": 55.3, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8477934", "name": "Leon Draisaitl", "team": "EDM",
        "position": "C", "age": 28, "experience": 9, "fa_type": "UFA",
        "aav": 8500000, "contract_years": 8, "expiry_season": 2025,
        "stats": {
            "games_played": 81, "goals": 42, "assists": 63, "points": 105,
            "plus_minus": 14, "toi_per_game": 22.2,
            "goals_per_60": 3.2, "assists_per_60": 4.7, "points_per_60": 7.9,
            "corsi_for_pct": 53.8, "xgf_pct": 54.5, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8480315", "name": "Brayden Point", "team": "TBL",
        "position": "C", "age": 28, "experience": 8, "fa_type": "UFA",
        "aav": 9500000, "contract_years": 8, "expiry_season": 2032,
        "stats": {
            "games_played": 82, "goals": 51, "assists": 60, "points": 111,
            "plus_minus": 22, "toi_per_game": 19.8,
            "goals_per_60": 4.0, "assists_per_60": 4.7, "points_per_60": 8.7,
            "corsi_for_pct": 55.0, "xgf_pct": 55.8, "penalty_diff_per_60": 0.1,
        },
    },
    {
        "player_id": "8480012", "name": "Elias Pettersson", "team": "VAN",
        "position": "C", "age": 25, "experience": 6, "fa_type": "UFA",
        "aav": 11600000, "contract_years": 8, "expiry_season": 2031,
        "stats": {
            "games_played": 82, "goals": 28, "assists": 74, "points": 102,
            "plus_minus": 18, "toi_per_game": 20.5,
            "goals_per_60": 2.2, "assists_per_60": 5.6, "points_per_60": 7.8,
            "corsi_for_pct": 52.5, "xgf_pct": 53.1, "penalty_diff_per_60": 0.3,
        },
    },
    {
        "player_id": "8479318", "name": "Jack Hughes", "team": "NJD",
        "position": "C", "age": 22, "experience": 5, "fa_type": "RFA",
        "aav": 8000000, "contract_years": 7, "expiry_season": 2026,
        "stats": {
            "games_played": 77, "goals": 37, "assists": 62, "points": 99,
            "plus_minus": 12, "toi_per_game": 20.8,
            "goals_per_60": 2.9, "assists_per_60": 4.8, "points_per_60": 7.7,
            "corsi_for_pct": 52.1, "xgf_pct": 53.0, "penalty_diff_per_60": 0.2,
        },
    },
    {
        "player_id": "8476456", "name": "Aleksander Barkov", "team": "FLA",
        "position": "C", "age": 28, "experience": 11, "fa_type": "UFA",
        "aav": 10000000, "contract_years": 8, "expiry_season": 2031,
        "stats": {
            "games_played": 72, "goals": 29, "assists": 52, "points": 81,
            "plus_minus": 17, "toi_per_game": 21.8,
            "goals_per_60": 2.3, "assists_per_60": 4.0, "points_per_60": 6.3,
            "corsi_for_pct": 56.5, "xgf_pct": 57.8, "penalty_diff_per_60": 0.8,
        },
    },
    {
        "player_id": "8458568", "name": "Sidney Crosby", "team": "PIT",
        "position": "C", "age": 36, "experience": 19, "fa_type": "UFA",
        "aav": 8700000, "contract_years": 2, "expiry_season": 2025,
        "stats": {
            "games_played": 82, "goals": 42, "assists": 52, "points": 94,
            "plus_minus": 18, "toi_per_game": 20.8,
            "goals_per_60": 3.2, "assists_per_60": 4.0, "points_per_60": 7.2,
            "corsi_for_pct": 53.5, "xgf_pct": 54.2, "penalty_diff_per_60": 0.3,
        },
    },
    {
        "player_id": "8475166", "name": "John Tavares", "team": "TOR",
        "position": "C", "age": 33, "experience": 15, "fa_type": "UFA",
        "aav": 11000000, "contract_years": 7, "expiry_season": 2025,
        "stats": {
            "games_played": 72, "goals": 28, "assists": 47, "points": 75,
            "plus_minus": 5, "toi_per_game": 19.5,
            "goals_per_60": 2.4, "assists_per_60": 4.0, "points_per_60": 6.4,
            "corsi_for_pct": 51.2, "xgf_pct": 51.8, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8476441", "name": "Mark Scheifele", "team": "WPG",
        "position": "C", "age": 31, "experience": 12, "fa_type": "UFA",
        "aav": 6125000, "contract_years": 7, "expiry_season": 2025,
        "stats": {
            "games_played": 75, "goals": 23, "assists": 52, "points": 75,
            "plus_minus": 6, "toi_per_game": 18.5,
            "goals_per_60": 2.0, "assists_per_60": 4.5, "points_per_60": 6.5,
            "corsi_for_pct": 50.8, "xgf_pct": 51.2, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8476459", "name": "Sean Couturier", "team": "PHI",
        "position": "C", "age": 31, "experience": 13, "fa_type": "UFA",
        "aav": 7750000, "contract_years": 8, "expiry_season": 2028,
        "stats": {
            "games_played": 79, "goals": 22, "assists": 41, "points": 63,
            "plus_minus": 10, "toi_per_game": 19.8,
            "goals_per_60": 1.8, "assists_per_60": 3.3, "points_per_60": 5.1,
            "corsi_for_pct": 52.8, "xgf_pct": 53.2, "penalty_diff_per_60": 0.5,
        },
    },
    {
        "player_id": "8480434", "name": "Bo Horvat", "team": "NYI",
        "position": "C", "age": 29, "experience": 10, "fa_type": "UFA",
        "aav": 8500000, "contract_years": 8, "expiry_season": 2031,
        "stats": {
            "games_played": 82, "goals": 31, "assists": 40, "points": 71,
            "plus_minus": 2, "toi_per_game": 18.8,
            "goals_per_60": 2.6, "assists_per_60": 3.3, "points_per_60": 5.9,
            "corsi_for_pct": 50.5, "xgf_pct": 51.0, "penalty_diff_per_60": 0.1,
        },
    },
    {
        "player_id": "8478476", "name": "Jack Eichel", "team": "VGK",
        "position": "C", "age": 27, "experience": 9, "fa_type": "UFA",
        "aav": 10000000, "contract_years": 8, "expiry_season": 2028,
        "stats": {
            "games_played": 78, "goals": 30, "assists": 50, "points": 80,
            "plus_minus": 12, "toi_per_game": 19.5,
            "goals_per_60": 2.5, "assists_per_60": 4.2, "points_per_60": 6.7,
            "corsi_for_pct": 52.0, "xgf_pct": 52.5, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8476468", "name": "Kyle Connor", "team": "WPG",
        "position": "LW", "age": 27, "experience": 7, "fa_type": "RFA",
        "aav": 7142000, "contract_years": 7, "expiry_season": 2026,
        "stats": {
            "games_played": 82, "goals": 33, "assists": 49, "points": 82,
            "plus_minus": 15, "toi_per_game": 18.5,
            "goals_per_60": 2.8, "assists_per_60": 4.1, "points_per_60": 6.9,
            "corsi_for_pct": 51.8, "xgf_pct": 52.2, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8481533", "name": "Nico Hischier", "team": "NJD",
        "position": "C", "age": 25, "experience": 7, "fa_type": "RFA",
        "aav": 7250000, "contract_years": 8, "expiry_season": 2026,
        "stats": {
            "games_played": 75, "goals": 25, "assists": 37, "points": 62,
            "plus_minus": 8, "toi_per_game": 19.0,
            "goals_per_60": 2.2, "assists_per_60": 3.2, "points_per_60": 5.4,
            "corsi_for_pct": 51.5, "xgf_pct": 51.8, "penalty_diff_per_60": 0.3,
        },
    },
    {
        "player_id": "8478455", "name": "Vincent Trocheck", "team": "NYR",
        "position": "C", "age": 31, "experience": 10, "fa_type": "UFA",
        "aav": 5625000, "contract_years": 7, "expiry_season": 2030,
        "stats": {
            "games_played": 82, "goals": 27, "assists": 41, "points": 68,
            "plus_minus": 10, "toi_per_game": 17.5,
            "goals_per_60": 2.5, "assists_per_60": 3.7, "points_per_60": 6.2,
            "corsi_for_pct": 51.0, "xgf_pct": 51.5, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8477406", "name": "Mika Zibanejad", "team": "NYR",
        "position": "C", "age": 31, "experience": 13, "fa_type": "UFA",
        "aav": 8500000, "contract_years": 8, "expiry_season": 2030,
        "stats": {
            "games_played": 73, "goals": 28, "assists": 38, "points": 66,
            "plus_minus": 8, "toi_per_game": 19.8,
            "goals_per_60": 2.4, "assists_per_60": 3.2, "points_per_60": 5.6,
            "corsi_for_pct": 51.8, "xgf_pct": 52.2, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8480382", "name": "Clayton Keller", "team": "ARI",
        "position": "C", "age": 25, "experience": 7, "fa_type": "RFA",
        "aav": 7150000, "contract_years": 8, "expiry_season": 2027,
        "stats": {
            "games_played": 82, "goals": 29, "assists": 47, "points": 76,
            "plus_minus": 5, "toi_per_game": 18.5,
            "goals_per_60": 2.5, "assists_per_60": 4.0, "points_per_60": 6.5,
            "corsi_for_pct": 50.8, "xgf_pct": 51.2, "penalty_diff_per_60": 0.0,
        },
    },

    # ─── ELITE WINGERS ────────────────────────────────────────────────────────
    {
        "player_id": "8476453", "name": "Nikita Kucherov", "team": "TBL",
        "position": "RW", "age": 31, "experience": 11, "fa_type": "UFA",
        "aav": 9500000, "contract_years": 9, "expiry_season": 2027,
        "stats": {
            "games_played": 82, "goals": 44, "assists": 100, "points": 144,
            "plus_minus": 36, "toi_per_game": 20.8,
            "goals_per_60": 3.3, "assists_per_60": 7.6, "points_per_60": 10.9,
            "corsi_for_pct": 56.0, "xgf_pct": 57.2, "penalty_diff_per_60": 0.2,
        },
    },
    {
        "player_id": "8477956", "name": "David Pastrnak", "team": "BOS",
        "position": "RW", "age": 27, "experience": 10, "fa_type": "UFA",
        "aav": 11250000, "contract_years": 8, "expiry_season": 2032,
        "stats": {
            "games_played": 82, "goals": 41, "assists": 60, "points": 101,
            "plus_minus": 18, "toi_per_game": 19.8,
            "goals_per_60": 3.2, "assists_per_60": 4.6, "points_per_60": 7.8,
            "corsi_for_pct": 54.2, "xgf_pct": 55.0, "penalty_diff_per_60": 0.1,
        },
    },
    {
        "player_id": "8481535", "name": "Matthew Tkachuk", "team": "FLA",
        "position": "LW", "age": 26, "experience": 7, "fa_type": "UFA",
        "aav": 9500000, "contract_years": 8, "expiry_season": 2031,
        "stats": {
            "games_played": 82, "goals": 27, "assists": 72, "points": 99,
            "plus_minus": 18, "toi_per_game": 20.5,
            "goals_per_60": 2.1, "assists_per_60": 5.6, "points_per_60": 7.7,
            "corsi_for_pct": 52.8, "xgf_pct": 53.5, "penalty_diff_per_60": 0.5,
        },
    },
    {
        "player_id": "8480762", "name": "Mikko Rantanen", "team": "COL",
        "position": "RW", "age": 27, "experience": 8, "fa_type": "UFA",
        "aav": 9250000, "contract_years": 5, "expiry_season": 2025,
        "stats": {
            "games_played": 82, "goals": 49, "assists": 56, "points": 105,
            "plus_minus": 24, "toi_per_game": 20.2,
            "goals_per_60": 3.7, "assists_per_60": 4.3, "points_per_60": 8.0,
            "corsi_for_pct": 54.5, "xgf_pct": 55.2, "penalty_diff_per_60": 0.1,
        },
    },
    {
        "player_id": "8479415", "name": "Kirill Kaprizov", "team": "MIN",
        "position": "LW", "age": 27, "experience": 4, "fa_type": "RFA",
        "aav": 9000000, "contract_years": 5, "expiry_season": 2027,
        "stats": {
            "games_played": 82, "goals": 35, "assists": 49, "points": 84,
            "plus_minus": 14, "toi_per_game": 19.5,
            "goals_per_60": 2.8, "assists_per_60": 3.8, "points_per_60": 6.6,
            "corsi_for_pct": 52.2, "xgf_pct": 52.8, "penalty_diff_per_60": 0.1,
        },
    },
    {
        "player_id": "8479341", "name": "Jason Robertson", "team": "DAL",
        "position": "LW", "age": 24, "experience": 5, "fa_type": "RFA",
        "aav": 7750000, "contract_years": 4, "expiry_season": 2027,
        "stats": {
            "games_played": 82, "goals": 37, "assists": 50, "points": 87,
            "plus_minus": 16, "toi_per_game": 18.8,
            "goals_per_60": 3.1, "assists_per_60": 4.1, "points_per_60": 7.2,
            "corsi_for_pct": 52.5, "xgf_pct": 53.0, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8479291", "name": "Tage Thompson", "team": "BUF",
        "position": "C", "age": 26, "experience": 7, "fa_type": "RFA",
        "aav": 7142000, "contract_years": 7, "expiry_season": 2028,
        "stats": {
            "games_played": 82, "goals": 47, "assists": 41, "points": 88,
            "plus_minus": 14, "toi_per_game": 18.8,
            "goals_per_60": 3.9, "assists_per_60": 3.3, "points_per_60": 7.2,
            "corsi_for_pct": 51.8, "xgf_pct": 52.2, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8476346", "name": "Mitch Marner", "team": "TOR",
        "position": "RW", "age": 26, "experience": 8, "fa_type": "UFA",
        "aav": 10893000, "contract_years": 6, "expiry_season": 2025,
        "stats": {
            "games_played": 74, "goals": 23, "assists": 57, "points": 80,
            "plus_minus": 15, "toi_per_game": 19.8,
            "goals_per_60": 1.9, "assists_per_60": 4.7, "points_per_60": 6.6,
            "corsi_for_pct": 52.8, "xgf_pct": 53.2, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8478550", "name": "Artemi Panarin", "team": "NYR",
        "position": "LW", "age": 32, "experience": 9, "fa_type": "UFA",
        "aav": 11642000, "contract_years": 7, "expiry_season": 2026,
        "stats": {
            "games_played": 79, "goals": 28, "assists": 61, "points": 89,
            "plus_minus": 18, "toi_per_game": 19.5,
            "goals_per_60": 2.3, "assists_per_60": 5.0, "points_per_60": 7.3,
            "corsi_for_pct": 53.5, "xgf_pct": 54.0, "penalty_diff_per_60": 0.1,
        },
    },
    {
        "player_id": "8477493", "name": "Mark Stone", "team": "VGK",
        "position": "RW", "age": 31, "experience": 12, "fa_type": "UFA",
        "aav": 9500000, "contract_years": 8, "expiry_season": 2027,
        "stats": {
            "games_played": 61, "goals": 18, "assists": 38, "points": 56,
            "plus_minus": 10, "toi_per_game": 18.8,
            "goals_per_60": 1.9, "assists_per_60": 4.0, "points_per_60": 5.9,
            "corsi_for_pct": 54.8, "xgf_pct": 55.2, "penalty_diff_per_60": 0.8,
        },
    },
    {
        "player_id": "8481522", "name": "Brady Tkachuk", "team": "OTT",
        "position": "LW", "age": 24, "experience": 6, "fa_type": "UFA",
        "aav": 9500000, "contract_years": 7, "expiry_season": 2028,
        "stats": {
            "games_played": 78, "goals": 28, "assists": 40, "points": 68,
            "plus_minus": 8, "toi_per_game": 18.5,
            "goals_per_60": 2.3, "assists_per_60": 3.3, "points_per_60": 5.6,
            "corsi_for_pct": 50.8, "xgf_pct": 51.2, "penalty_diff_per_60": 1.2,
        },
    },
    {
        "player_id": "8481600", "name": "Sam Reinhart", "team": "FLA",
        "position": "RW", "age": 28, "experience": 9, "fa_type": "UFA",
        "aav": 8000000, "contract_years": 8, "expiry_season": 2032,
        "stats": {
            "games_played": 82, "goals": 57, "assists": 57, "points": 114,
            "plus_minus": 26, "toi_per_game": 19.0,
            "goals_per_60": 4.5, "assists_per_60": 4.5, "points_per_60": 9.0,
            "corsi_for_pct": 52.5, "xgf_pct": 53.0, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8476887", "name": "Filip Forsberg", "team": "NSH",
        "position": "LW", "age": 30, "experience": 11, "fa_type": "UFA",
        "aav": 8500000, "contract_years": 8, "expiry_season": 2030,
        "stats": {
            "games_played": 82, "goals": 28, "assists": 49, "points": 77,
            "plus_minus": 12, "toi_per_game": 19.5,
            "goals_per_60": 2.3, "assists_per_60": 4.0, "points_per_60": 6.3,
            "corsi_for_pct": 51.5, "xgf_pct": 52.0, "penalty_diff_per_60": 0.1,
        },
    },
    {
        "player_id": "8476474", "name": "Tom Wilson", "team": "WSH",
        "position": "RW", "age": 30, "experience": 11, "fa_type": "UFA",
        "aav": 6500000, "contract_years": 7, "expiry_season": 2028,
        "stats": {
            "games_played": 78, "goals": 26, "assists": 44, "points": 70,
            "plus_minus": 14, "toi_per_game": 17.8,
            "goals_per_60": 2.3, "assists_per_60": 3.9, "points_per_60": 6.2,
            "corsi_for_pct": 51.2, "xgf_pct": 51.8, "penalty_diff_per_60": 0.8,
        },
    },
    {
        "player_id": "8475793", "name": "Chris Kreider", "team": "NYR",
        "position": "LW", "age": 33, "experience": 12, "fa_type": "UFA",
        "aav": 6500000, "contract_years": 7, "expiry_season": 2028,
        "stats": {
            "games_played": 82, "goals": 39, "assists": 29, "points": 68,
            "plus_minus": 12, "toi_per_game": 15.5,
            "goals_per_60": 4.0, "assists_per_60": 3.0, "points_per_60": 7.0,
            "corsi_for_pct": 50.5, "xgf_pct": 51.0, "penalty_diff_per_60": 0.2,
        },
    },
    {
        "player_id": "8478509", "name": "Elias Lindholm", "team": "BOS",
        "position": "C", "age": 29, "experience": 11, "fa_type": "UFA",
        "aav": 8650000, "contract_years": 8, "expiry_season": 2032,
        "stats": {
            "games_played": 74, "goals": 27, "assists": 40, "points": 67,
            "plus_minus": 10, "toi_per_game": 18.8,
            "goals_per_60": 2.3, "assists_per_60": 3.3, "points_per_60": 5.6,
            "corsi_for_pct": 52.5, "xgf_pct": 53.0, "penalty_diff_per_60": 0.3,
        },
    },
    {
        "player_id": "8480023", "name": "Jordan Kyrou", "team": "STL",
        "position": "RW", "age": 26, "experience": 6, "fa_type": "RFA",
        "aav": 7000000, "contract_years": 8, "expiry_season": 2030,
        "stats": {
            "games_played": 80, "goals": 32, "assists": 43, "points": 75,
            "plus_minus": 9, "toi_per_game": 17.8,
            "goals_per_60": 2.8, "assists_per_60": 3.7, "points_per_60": 6.5,
            "corsi_for_pct": 51.0, "xgf_pct": 51.5, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8475462", "name": "Ryan O'Reilly", "team": "NSH",
        "position": "C", "age": 33, "experience": 14, "fa_type": "UFA",
        "aav": 7500000, "contract_years": 8, "expiry_season": 2026,
        "stats": {
            "games_played": 74, "goals": 18, "assists": 37, "points": 55,
            "plus_minus": 8, "toi_per_game": 17.8,
            "goals_per_60": 1.6, "assists_per_60": 3.3, "points_per_60": 4.9,
            "corsi_for_pct": 52.0, "xgf_pct": 52.5, "penalty_diff_per_60": 0.5,
        },
    },
    {
        "player_id": "8475225", "name": "Ryan Nugent-Hopkins", "team": "EDM",
        "position": "LW", "age": 31, "experience": 13, "fa_type": "UFA",
        "aav": 5125000, "contract_years": 8, "expiry_season": 2029,
        "stats": {
            "games_played": 80, "goals": 18, "assists": 44, "points": 62,
            "plus_minus": 12, "toi_per_game": 17.5,
            "goals_per_60": 1.6, "assists_per_60": 3.9, "points_per_60": 5.5,
            "corsi_for_pct": 51.8, "xgf_pct": 52.2, "penalty_diff_per_60": 0.3,
        },
    },
    {
        "player_id": "8480435", "name": "Carter Verhaeghe", "team": "FLA",
        "position": "LW", "age": 28, "experience": 5, "fa_type": "UFA",
        "aav": 5250000, "contract_years": 4, "expiry_season": 2027,
        "stats": {
            "games_played": 78, "goals": 30, "assists": 36, "points": 66,
            "plus_minus": 14, "toi_per_game": 16.5,
            "goals_per_60": 2.9, "assists_per_60": 3.4, "points_per_60": 6.3,
            "corsi_for_pct": 51.2, "xgf_pct": 51.8, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8476925", "name": "Claude Giroux", "team": "OTT",
        "position": "RW", "age": 36, "experience": 18, "fa_type": "UFA",
        "aav": 6500000, "contract_years": 3, "expiry_season": 2025,
        "stats": {
            "games_played": 82, "goals": 15, "assists": 41, "points": 56,
            "plus_minus": 4, "toi_per_game": 17.2,
            "goals_per_60": 1.3, "assists_per_60": 3.5, "points_per_60": 4.8,
            "corsi_for_pct": 50.2, "xgf_pct": 50.8, "penalty_diff_per_60": 0.1,
        },
    },
    {
        "player_id": "8476839", "name": "Tyler Seguin", "team": "DAL",
        "position": "C", "age": 32, "experience": 14, "fa_type": "UFA",
        "aav": 9857000, "contract_years": 8, "expiry_season": 2026,
        "stats": {
            "games_played": 77, "goals": 26, "assists": 38, "points": 64,
            "plus_minus": 5, "toi_per_game": 18.5,
            "goals_per_60": 2.2, "assists_per_60": 3.3, "points_per_60": 5.5,
            "corsi_for_pct": 50.8, "xgf_pct": 51.2, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8476462", "name": "Jonathan Huberdeau", "team": "CGY",
        "position": "LW", "age": 30, "experience": 12, "fa_type": "UFA",
        "aav": 10500000, "contract_years": 8, "expiry_season": 2030,
        "stats": {
            "games_played": 80, "goals": 23, "assists": 43, "points": 66,
            "plus_minus": 3, "toi_per_game": 17.8,
            "goals_per_60": 1.9, "assists_per_60": 3.6, "points_per_60": 5.5,
            "corsi_for_pct": 50.5, "xgf_pct": 51.0, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8476344", "name": "Jake Guentzel", "team": "TBL",
        "position": "LW", "age": 29, "experience": 8, "fa_type": "UFA",
        "aav": 6000000, "contract_years": 1, "expiry_season": 2024,
        "stats": {
            "games_played": 69, "goals": 30, "assists": 38, "points": 68,
            "plus_minus": 14, "toi_per_game": 17.5,
            "goals_per_60": 2.7, "assists_per_60": 3.4, "points_per_60": 6.1,
            "corsi_for_pct": 51.5, "xgf_pct": 52.0, "penalty_diff_per_60": 0.0,
        },
    },
    {
        "player_id": "8475765", "name": "Steven Stamkos", "team": "NSH",
        "position": "C", "age": 34, "experience": 16, "fa_type": "UFA",
        "aav": 8000000, "contract_years": 4, "expiry_season": 2028,
        "stats": {
            "games_played": 75, "goals": 28, "assists": 37, "points": 65,
            "plus_minus": 8, "toi_per_game": 17.5,
            "goals_per_60": 2.4, "assists_per_60": 3.2, "points_per_60": 5.6,
            "corsi_for_pct": 50.5, "xgf_pct": 51.0, "penalty_diff_per_60": 0.1,
        },
    },

    # ─── DEFENSEMEN ──────────────────────────────────────────────────────────
    {
        "player_id": "8480069", "name": "Cale Makar", "team": "COL",
        "position": "D", "age": 25, "experience": 5, "fa_type": "UFA",
        "aav": 9000000, "contract_years": 6, "expiry_season": 2029,
        "stats": {
            "games_played": 82, "goals": 21, "assists": 48, "points": 69,
            "plus_minus": 29, "toi_per_game": 25.2,
            "goals_per_60": 1.3, "assists_per_60": 2.9, "points_per_60": 4.2,
            "corsi_for_pct": 56.8, "xgf_pct": 57.5, "penalty_diff_per_60": -0.1,
        },
    },
    {
        "player_id": "8474578", "name": "Erik Karlsson", "team": "PIT",
        "position": "D", "age": 34, "experience": 15, "fa_type": "UFA",
        "aav": 11500000, "contract_years": 8, "expiry_season": 2027,
        "stats": {
            "games_played": 81, "goals": 10, "assists": 46, "points": 56,
            "plus_minus": 2, "toi_per_game": 24.5,
            "goals_per_60": 0.6, "assists_per_60": 2.8, "points_per_60": 3.4,
            "corsi_for_pct": 51.5, "xgf_pct": 52.0, "penalty_diff_per_60": -0.1,
        },
    },
    {
        "player_id": "8474600", "name": "Roman Josi", "team": "NSH",
        "position": "D", "age": 33, "experience": 13, "fa_type": "UFA",
        "aav": 9059000, "contract_years": 8, "expiry_season": 2027,
        "stats": {
            "games_played": 82, "goals": 16, "assists": 56, "points": 72,
            "plus_minus": 18, "toi_per_game": 25.8,
            "goals_per_60": 0.9, "assists_per_60": 3.2, "points_per_60": 4.1,
            "corsi_for_pct": 53.2, "xgf_pct": 53.8, "penalty_diff_per_60": -0.1,
        },
    },
    {
        "player_id": "8475743", "name": "Seth Jones", "team": "CHI",
        "position": "D", "age": 29, "experience": 11, "fa_type": "UFA",
        "aav": 9500000, "contract_years": 8, "expiry_season": 2029,
        "stats": {
            "games_played": 80, "goals": 14, "assists": 44, "points": 58,
            "plus_minus": 6, "toi_per_game": 25.5,
            "goals_per_60": 0.8, "assists_per_60": 2.5, "points_per_60": 3.3,
            "corsi_for_pct": 52.0, "xgf_pct": 52.5, "penalty_diff_per_60": -0.2,
        },
    },
    {
        "player_id": "8481546", "name": "Adam Fox", "team": "NYR",
        "position": "D", "age": 26, "experience": 5, "fa_type": "RFA",
        "aav": 9500000, "contract_years": 7, "expiry_season": 2029,
        "stats": {
            "games_played": 82, "goals": 10, "assists": 60, "points": 70,
            "plus_minus": 22, "toi_per_game": 24.2,
            "goals_per_60": 0.6, "assists_per_60": 3.6, "points_per_60": 4.2,
            "corsi_for_pct": 54.5, "xgf_pct": 55.0, "penalty_diff_per_60": -0.1,
        },
    },
    {
        "player_id": "8481608", "name": "Quinn Hughes", "team": "VAN",
        "position": "D", "age": 24, "experience": 5, "fa_type": "RFA",
        "aav": 7850000, "contract_years": 8, "expiry_season": 2029,
        "stats": {
            "games_played": 82, "goals": 8, "assists": 63, "points": 71,
            "plus_minus": 18, "toi_per_game": 25.0,
            "goals_per_60": 0.5, "assists_per_60": 3.7, "points_per_60": 4.2,
            "corsi_for_pct": 53.8, "xgf_pct": 54.5, "penalty_diff_per_60": -0.1,
        },
    },
    {
        "player_id": "8480800", "name": "Rasmus Dahlin", "team": "BUF",
        "position": "D", "age": 23, "experience": 6, "fa_type": "RFA",
        "aav": 8150000, "contract_years": 8, "expiry_season": 2030,
        "stats": {
            "games_played": 82, "goals": 11, "assists": 51, "points": 62,
            "plus_minus": 14, "toi_per_game": 24.5,
            "goals_per_60": 0.7, "assists_per_60": 3.0, "points_per_60": 3.7,
            "corsi_for_pct": 52.8, "xgf_pct": 53.2, "penalty_diff_per_60": -0.1,
        },
    },
    {
        "player_id": "8480830", "name": "Noah Dobson", "team": "NYI",
        "position": "D", "age": 24, "experience": 5, "fa_type": "RFA",
        "aav": 7000000, "contract_years": 8, "expiry_season": 2031,
        "stats": {
            "games_played": 80, "goals": 9, "assists": 52, "points": 61,
            "plus_minus": 10, "toi_per_game": 24.0,
            "goals_per_60": 0.6, "assists_per_60": 3.2, "points_per_60": 3.8,
            "corsi_for_pct": 51.5, "xgf_pct": 52.0, "penalty_diff_per_60": -0.1,
        },
    },
    {
        "player_id": "8477932", "name": "Dougie Hamilton", "team": "NJD",
        "position": "D", "age": 30, "experience": 12, "fa_type": "UFA",
        "aav": 9000000, "contract_years": 7, "expiry_season": 2028,
        "stats": {
            "games_played": 72, "goals": 12, "assists": 51, "points": 63,
            "plus_minus": 12, "toi_per_game": 24.2,
            "goals_per_60": 0.8, "assists_per_60": 3.2, "points_per_60": 4.0,
            "corsi_for_pct": 52.5, "xgf_pct": 53.0, "penalty_diff_per_60": -0.1,
        },
    },
    {
        "player_id": "8480948", "name": "Charlie McAvoy", "team": "BOS",
        "position": "D", "age": 26, "experience": 7, "fa_type": "RFA",
        "aav": 9500000, "contract_years": 8, "expiry_season": 2031,
        "stats": {
            "games_played": 82, "goals": 7, "assists": 40, "points": 47,
            "plus_minus": 14, "toi_per_game": 24.8,
            "goals_per_60": 0.4, "assists_per_60": 2.4, "points_per_60": 2.8,
            "corsi_for_pct": 53.5, "xgf_pct": 54.0, "penalty_diff_per_60": -0.2,
        },
    },
    {
        "player_id": "8480493", "name": "Miro Heiskanen", "team": "DAL",
        "position": "D", "age": 24, "experience": 6, "fa_type": "RFA",
        "aav": 8450000, "contract_years": 8, "expiry_season": 2031,
        "stats": {
            "games_played": 82, "goals": 10, "assists": 42, "points": 52,
            "plus_minus": 10, "toi_per_game": 24.5,
            "goals_per_60": 0.6, "assists_per_60": 2.6, "points_per_60": 3.2,
            "corsi_for_pct": 52.8, "xgf_pct": 53.2, "penalty_diff_per_60": -0.2,
        },
    },
    {
        "player_id": "8475780", "name": "Victor Hedman", "team": "TBL",
        "position": "D", "age": 33, "experience": 14, "fa_type": "UFA",
        "aav": 7875000, "contract_years": 8, "expiry_season": 2025,
        "stats": {
            "games_played": 78, "goals": 11, "assists": 45, "points": 56,
            "plus_minus": 15, "toi_per_game": 25.5,
            "goals_per_60": 0.7, "assists_per_60": 2.8, "points_per_60": 3.5,
            "corsi_for_pct": 54.5, "xgf_pct": 55.0, "penalty_diff_per_60": -0.2,
        },
    },
    {
        "player_id": "8471694", "name": "John Carlson", "team": "WSH",
        "position": "D", "age": 33, "experience": 15, "fa_type": "UFA",
        "aav": 8000000, "contract_years": 8, "expiry_season": 2026,
        "stats": {
            "games_played": 72, "goals": 8, "assists": 37, "points": 45,
            "plus_minus": 8, "toi_per_game": 22.5,
            "goals_per_60": 0.5, "assists_per_60": 2.4, "points_per_60": 2.9,
            "corsi_for_pct": 51.5, "xgf_pct": 52.0, "penalty_diff_per_60": -0.1,
        },
    },
    {
        "player_id": "8470620", "name": "Drew Doughty", "team": "LAK",
        "position": "D", "age": 34, "experience": 16, "fa_type": "UFA",
        "aav": 11000000, "contract_years": 8, "expiry_season": 2025,
        "stats": {
            "games_played": 75, "goals": 9, "assists": 34, "points": 43,
            "plus_minus": 2, "toi_per_game": 24.2,
            "goals_per_60": 0.6, "assists_per_60": 2.2, "points_per_60": 2.8,
            "corsi_for_pct": 51.0, "xgf_pct": 51.5, "penalty_diff_per_60": -0.2,
        },
    },
    {
        "player_id": "8480768", "name": "Mikhail Sergachev", "team": "TBL",
        "position": "D", "age": 25, "experience": 7, "fa_type": "RFA",
        "aav": 8500000, "contract_years": 8, "expiry_season": 2031,
        "stats": {
            "games_played": 75, "goals": 8, "assists": 33, "points": 41,
            "plus_minus": 10, "toi_per_game": 23.2,
            "goals_per_60": 0.5, "assists_per_60": 2.1, "points_per_60": 2.6,
            "corsi_for_pct": 52.0, "xgf_pct": 52.5, "penalty_diff_per_60": -0.2,
        },
    },
    {
        "player_id": "8478398", "name": "Aaron Ekblad", "team": "FLA",
        "position": "D", "age": 28, "experience": 10, "fa_type": "UFA",
        "aav": 7500000, "contract_years": 8, "expiry_season": 2027,
        "stats": {
            "games_played": 74, "goals": 10, "assists": 32, "points": 42,
            "plus_minus": 6, "toi_per_game": 24.0,
            "goals_per_60": 0.6, "assists_per_60": 2.0, "points_per_60": 2.6,
            "corsi_for_pct": 51.8, "xgf_pct": 52.2, "penalty_diff_per_60": -0.2,
        },
    },
    {
        "player_id": "8477497", "name": "Darnell Nurse", "team": "EDM",
        "position": "D", "age": 29, "experience": 10, "fa_type": "UFA",
        "aav": 9250000, "contract_years": 8, "expiry_season": 2030,
        "stats": {
            "games_played": 74, "goals": 5, "assists": 24, "points": 29,
            "plus_minus": 2, "toi_per_game": 23.5,
            "goals_per_60": 0.3, "assists_per_60": 1.5, "points_per_60": 1.8,
            "corsi_for_pct": 50.5, "xgf_pct": 51.0, "penalty_diff_per_60": -0.3,
        },
    },
    {
        "player_id": "8475798", "name": "Morgan Rielly", "team": "TOR",
        "position": "D", "age": 29, "experience": 11, "fa_type": "UFA",
        "aav": 7500000, "contract_years": 8, "expiry_season": 2030,
        "stats": {
            "games_played": 76, "goals": 9, "assists": 36, "points": 45,
            "plus_minus": 4, "toi_per_game": 22.2,
            "goals_per_60": 0.6, "assists_per_60": 2.3, "points_per_60": 2.9,
            "corsi_for_pct": 51.0, "xgf_pct": 51.5, "penalty_diff_per_60": -0.1,
        },
    },
    {
        "player_id": "8480145", "name": "Evan Bouchard", "team": "EDM",
        "position": "D", "age": 24, "experience": 5, "fa_type": "RFA",
        "aav": 7500000, "contract_years": 8, "expiry_season": 2032,
        "stats": {
            "games_played": 82, "goals": 16, "assists": 55, "points": 71,
            "plus_minus": 16, "toi_per_game": 23.5,
            "goals_per_60": 1.0, "assists_per_60": 3.5, "points_per_60": 4.5,
            "corsi_for_pct": 52.8, "xgf_pct": 53.2, "penalty_diff_per_60": -0.1,
        },
    },
    {
        "player_id": "8483390", "name": "Jake Sanderson", "team": "OTT",
        "position": "D", "age": 22, "experience": 3, "fa_type": "RFA",
        "aav": 8500000, "contract_years": 8, "expiry_season": 2032,
        "stats": {
            "games_played": 72, "goals": 8, "assists": 33, "points": 41,
            "plus_minus": 8, "toi_per_game": 23.0,
            "goals_per_60": 0.5, "assists_per_60": 2.1, "points_per_60": 2.6,
            "corsi_for_pct": 52.5, "xgf_pct": 53.0, "penalty_diff_per_60": -0.1,
        },
    },
    {
        "player_id": "8482469", "name": "Moritz Seider", "team": "DET",
        "position": "D", "age": 23, "experience": 3, "fa_type": "RFA",
        "aav": 7000000, "contract_years": 7, "expiry_season": 2030,
        "stats": {
            "games_played": 75, "goals": 7, "assists": 28, "points": 35,
            "plus_minus": 3, "toi_per_game": 23.2,
            "goals_per_60": 0.5, "assists_per_60": 1.7, "points_per_60": 2.2,
            "corsi_for_pct": 51.2, "xgf_pct": 51.8, "penalty_diff_per_60": -0.2,
        },
    },
    {
        "player_id": "8478406", "name": "Gustav Forsling", "team": "FLA",
        "position": "D", "age": 28, "experience": 7, "fa_type": "RFA",
        "aav": 5900000, "contract_years": 4, "expiry_season": 2026,
        "stats": {
            "games_played": 80, "goals": 7, "assists": 34, "points": 41,
            "plus_minus": 12, "toi_per_game": 22.8,
            "goals_per_60": 0.5, "assists_per_60": 2.2, "points_per_60": 2.7,
            "corsi_for_pct": 52.2, "xgf_pct": 52.8, "penalty_diff_per_60": -0.1,
        },
    },
    {
        "player_id": "8477457", "name": "Jaccob Slavin", "team": "CAR",
        "position": "D", "age": 30, "experience": 9, "fa_type": "UFA",
        "aav": 5300000, "contract_years": 7, "expiry_season": 2025,
        "stats": {
            "games_played": 82, "goals": 5, "assists": 28, "points": 33,
            "plus_minus": 15, "toi_per_game": 23.0,
            "goals_per_60": 0.3, "assists_per_60": 1.8, "points_per_60": 2.1,
            "corsi_for_pct": 54.2, "xgf_pct": 54.8, "penalty_diff_per_60": -0.3,
        },
    },
    {
        "player_id": "8475831", "name": "Torey Krug", "team": "STL",
        "position": "D", "age": 33, "experience": 12, "fa_type": "UFA",
        "aav": 6500000, "contract_years": 7, "expiry_season": 2028,
        "stats": {
            "games_played": 75, "goals": 8, "assists": 34, "points": 42,
            "plus_minus": 6, "toi_per_game": 21.5,
            "goals_per_60": 0.6, "assists_per_60": 2.4, "points_per_60": 3.0,
            "corsi_for_pct": 51.5, "xgf_pct": 52.0, "penalty_diff_per_60": -0.1,
        },
    },
    {
        "player_id": "8479323", "name": "Devon Toews", "team": "COL",
        "position": "D", "age": 30, "experience": 7, "fa_type": "RFA",
        "aav": 4100000, "contract_years": 4, "expiry_season": 2025,
        "stats": {
            "games_played": 76, "goals": 5, "assists": 32, "points": 37,
            "plus_minus": 14, "toi_per_game": 23.2,
            "goals_per_60": 0.3, "assists_per_60": 2.0, "points_per_60": 2.3,
            "corsi_for_pct": 55.2, "xgf_pct": 55.8, "penalty_diff_per_60": -0.2,
        },
    },

    # ─── GOALIES ─────────────────────────────────────────────────────────────
    {
        "player_id": "8478009", "name": "Igor Shesterkin", "team": "NYR",
        "position": "G", "age": 28, "experience": 5, "fa_type": "UFA",
        "aav": 8500000, "contract_years": 4, "expiry_season": 2027,
        "stats": {
            "games_played": 58, "games_started": 55,
            "gaa": 2.41, "save_pct": 0.913, "quality_start_pct": 0.618,
        },
    },
    {
        "player_id": "8476883", "name": "Andrei Vasilevskiy", "team": "TBL",
        "position": "G", "age": 29, "experience": 10, "fa_type": "UFA",
        "aav": 9500000, "contract_years": 8, "expiry_season": 2028,
        "stats": {
            "games_played": 65, "games_started": 62,
            "gaa": 2.65, "save_pct": 0.908, "quality_start_pct": 0.595,
        },
    },
    {
        "player_id": "8476412", "name": "Connor Hellebuyck", "team": "WPG",
        "position": "G", "age": 31, "experience": 10, "fa_type": "UFA",
        "aav": 6170000, "contract_years": 6, "expiry_season": 2025,
        "stats": {
            "games_played": 60, "games_started": 59,
            "gaa": 2.39, "save_pct": 0.921, "quality_start_pct": 0.636,
        },
    },
    {
        "player_id": "8482235", "name": "Jeremy Swayman", "team": "BOS",
        "position": "G", "age": 25, "experience": 4, "fa_type": "RFA",
        "aav": 8250000, "contract_years": 8, "expiry_season": 2032,
        "stats": {
            "games_played": 64, "games_started": 62,
            "gaa": 2.56, "save_pct": 0.918, "quality_start_pct": 0.619,
        },
    },
    {
        "player_id": "8480353", "name": "Ilya Sorokin", "team": "NYI",
        "position": "G", "age": 28, "experience": 4, "fa_type": "RFA",
        "aav": 7500000, "contract_years": 4, "expiry_season": 2026,
        "stats": {
            "games_played": 62, "games_started": 59,
            "gaa": 2.91, "save_pct": 0.902, "quality_start_pct": 0.576,
        },
    },
    {
        "player_id": "8477446", "name": "Juuse Saros", "team": "NSH",
        "position": "G", "age": 29, "experience": 8, "fa_type": "UFA",
        "aav": 4950000, "contract_years": 4, "expiry_season": 2025,
        "stats": {
            "games_played": 55, "games_started": 52,
            "gaa": 2.51, "save_pct": 0.917, "quality_start_pct": 0.615,
        },
    },
    {
        "player_id": "8481577", "name": "Jake Oettinger", "team": "DAL",
        "position": "G", "age": 25, "experience": 4, "fa_type": "RFA",
        "aav": 4500000, "contract_years": 3, "expiry_season": 2026,
        "stats": {
            "games_played": 64, "games_started": 61,
            "gaa": 2.91, "save_pct": 0.906, "quality_start_pct": 0.590,
        },
    },
    {
        "player_id": "8475852", "name": "Jordan Binnington", "team": "STL",
        "position": "G", "age": 30, "experience": 6, "fa_type": "UFA",
        "aav": 6000000, "contract_years": 6, "expiry_season": 2028,
        "stats": {
            "games_played": 60, "games_started": 58,
            "gaa": 2.75, "save_pct": 0.911, "quality_start_pct": 0.605,
        },
    },
    {
        "player_id": "8477073", "name": "Tristan Jarry", "team": "PIT",
        "position": "G", "age": 29, "experience": 7, "fa_type": "UFA",
        "aav": 5375000, "contract_years": 5, "expiry_season": 2027,
        "stats": {
            "games_played": 51, "games_started": 49,
            "gaa": 2.96, "save_pct": 0.898, "quality_start_pct": 0.571,
        },
    },
    {
        "player_id": "8478449", "name": "Thatcher Demko", "team": "VAN",
        "position": "G", "age": 28, "experience": 5, "fa_type": "RFA",
        "aav": 5000000, "contract_years": 3, "expiry_season": 2025,
        "stats": {
            "games_played": 54, "games_started": 52,
            "gaa": 2.81, "save_pct": 0.912, "quality_start_pct": 0.600,
        },
    },
    {
        "player_id": "8475883", "name": "Sergei Bobrovsky", "team": "FLA",
        "position": "G", "age": 36, "experience": 14, "fa_type": "UFA",
        "aav": 10000000, "contract_years": 7, "expiry_season": 2026,
        "stats": {
            "games_played": 58, "games_started": 55,
            "gaa": 2.72, "save_pct": 0.912, "quality_start_pct": 0.600,
        },
    },
    {
        "player_id": "8476892", "name": "Linus Ullmark", "team": "OTT",
        "position": "G", "age": 30, "experience": 8, "fa_type": "UFA",
        "aav": 5000000, "contract_years": 4, "expiry_season": 2024,
        "stats": {
            "games_played": 55, "games_started": 52,
            "gaa": 2.51, "save_pct": 0.921, "quality_start_pct": 0.635,
        },
    },
    {
        "player_id": "8483525", "name": "Pyotr Kochetkov", "team": "CAR",
        "position": "G", "age": 24, "experience": 3, "fa_type": "RFA",
        "aav": 4500000, "contract_years": 3, "expiry_season": 2026,
        "stats": {
            "games_played": 50, "games_started": 47,
            "gaa": 2.71, "save_pct": 0.914, "quality_start_pct": 0.605,
        },
    },
    {
        "player_id": "8481532", "name": "Stuart Skinner", "team": "EDM",
        "position": "G", "age": 25, "experience": 3, "fa_type": "RFA",
        "aav": 2550000, "contract_years": 3, "expiry_season": 2025,
        "stats": {
            "games_played": 55, "games_started": 52,
            "gaa": 2.95, "save_pct": 0.901, "quality_start_pct": 0.569,
        },
    },
    {
        "player_id": "8471418", "name": "Marc-Andre Fleury", "team": "MIN",
        "position": "G", "age": 39, "experience": 20, "fa_type": "UFA",
        "aav": 3500000, "contract_years": 1, "expiry_season": 2024,
        "stats": {
            "games_played": 45, "games_started": 44,
            "gaa": 2.95, "save_pct": 0.899, "quality_start_pct": 0.555,
        },
    },
]


def get_seed_players():
    return SEED_PLAYERS
