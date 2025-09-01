import React from 'react';
import { Trophy, TrendingUp, Award } from 'lucide-react';

export function LeaderboardPage() {
  // Mock data for demonstration
  const leaderboard = [
    { rank: 1, name: 'Champion123', elo: 2150, wins: 145, losses: 32 },
    { rank: 2, name: 'WordMaster', elo: 2089, wins: 98, losses: 24 },
    { rank: 3, name: 'NumberWiz', elo: 1987, wins: 76, losses: 28 },
    { rank: 4, name: 'QuickThinker', elo: 1876, wins: 64, losses: 31 },
    { rank: 5, name: 'BrainStorm', elo: 1823, wins: 52, losses: 29 },
  ];

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-4xl font-bold text-center mb-8 flex items-center justify-center">
        <Trophy className="w-10 h-10 mr-3 text-yellow-400" />
        Global Leaderboard
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <Trophy className="w-8 h-8 text-yellow-400 mr-3" />
            <div>
              <h3 className="text-2xl font-bold">Champion123</h3>
              <p className="text-gray-400">Current Champion</p>
            </div>
          </div>
          <div className="text-3xl font-bold text-yellow-400">2150 ELO</div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <TrendingUp className="w-8 h-8 text-green-400 mr-3" />
            <div>
              <h3 className="text-xl font-bold">Rising Star</h3>
              <p className="text-gray-400">QuickThinker</p>
            </div>
          </div>
          <div className="text-2xl font-bold text-green-400">+124 this week</div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <Award className="w-8 h-8 text-purple-400 mr-3" />
            <div>
              <h3 className="text-xl font-bold">Most Active</h3>
              <p className="text-gray-400">WordMaster</p>
            </div>
          </div>
          <div className="text-2xl font-bold text-purple-400">122 games</div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Rank
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Player
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                ELO Rating
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                W/L
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Win Rate
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {leaderboard.map((player) => {
              const winRate = ((player.wins / (player.wins + player.losses)) * 100).toFixed(1);
              return (
                <tr key={player.rank} className="hover:bg-gray-700/50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {player.rank === 1 && <Trophy className="w-5 h-5 text-yellow-400 mr-2" />}
                      {player.rank === 2 && <Trophy className="w-5 h-5 text-gray-400 mr-2" />}
                      {player.rank === 3 && <Trophy className="w-5 h-5 text-orange-600 mr-2" />}
                      <span className="text-lg font-bold">#{player.rank}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-lg font-medium">{player.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-lg font-bold text-blue-400">{player.elo}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-green-400">{player.wins}W</span>
                    <span className="text-gray-400"> / </span>
                    <span className="text-red-400">{player.losses}L</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-lg">{winRate}%</div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}