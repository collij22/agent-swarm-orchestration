import React from 'react';
import { Link } from 'react-router-dom';
import { Brain, Users, Trophy, BookOpen } from 'lucide-react';

export function HomePage() {
  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold text-blue-400 mb-4">
          Welcome to Countdown
        </h1>
        <p className="text-xl text-gray-300">
          Test your word and number skills in this classic game show format!
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Link
          to="/play"
          className="bg-gray-800 rounded-lg p-6 hover:bg-gray-700 transition-colors"
        >
          <Brain className="w-12 h-12 text-blue-400 mb-4" />
          <h2 className="text-2xl font-bold mb-2">Single Player</h2>
          <p className="text-gray-400">
            Play against AI opponents of varying difficulty levels
          </p>
        </Link>

        <Link
          to="/multiplayer"
          className="bg-gray-800 rounded-lg p-6 hover:bg-gray-700 transition-colors"
        >
          <Users className="w-12 h-12 text-green-400 mb-4" />
          <h2 className="text-2xl font-bold mb-2">Multiplayer</h2>
          <p className="text-gray-400">
            Challenge friends or compete with players worldwide
          </p>
        </Link>

        <Link
          to="/leaderboard"
          className="bg-gray-800 rounded-lg p-6 hover:bg-gray-700 transition-colors"
        >
          <Trophy className="w-12 h-12 text-yellow-400 mb-4" />
          <h2 className="text-2xl font-bold mb-2">Leaderboard</h2>
          <p className="text-gray-400">
            See how you rank against the best players
          </p>
        </Link>
      </div>

      <div className="mt-12 bg-gray-800 rounded-lg p-8">
        <h2 className="text-3xl font-bold mb-4 flex items-center">
          <BookOpen className="w-8 h-8 mr-2 text-purple-400" />
          How to Play
        </h2>
        <div className="space-y-4 text-gray-300">
          <div>
            <h3 className="text-xl font-semibold text-blue-400 mb-2">Letters Rounds</h3>
            <p>
              Select 9 letters (vowels and consonants) and make the longest word possible.
              Score 1 point per letter, with 18 points for a 9-letter word!
            </p>
          </div>
          <div>
            <h3 className="text-xl font-semibold text-green-400 mb-2">Numbers Rounds</h3>
            <p>
              Use 6 numbers to reach a target between 100-999. Score 10 points for exact,
              7 points for ±5, or 5 points for ±10.
            </p>
          </div>
          <div>
            <h3 className="text-xl font-semibold text-purple-400 mb-2">Conundrum</h3>
            <p>
              Solve a 9-letter anagram in the final round. First to buzz in and answer
              correctly wins 10 points!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}