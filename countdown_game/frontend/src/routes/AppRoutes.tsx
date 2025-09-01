import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { HomePage } from '../pages/HomePage';
import { PlayPage } from '../pages/PlayPage';
import { MultiplayerPage } from '../pages/MultiplayerPage';
import { LeaderboardPage } from '../pages/LeaderboardPage';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/play" element={<PlayPage />} />
      <Route path="/multiplayer" element={<MultiplayerPage />} />
      <Route path="/leaderboard" element={<LeaderboardPage />} />
    </Routes>
  );
}