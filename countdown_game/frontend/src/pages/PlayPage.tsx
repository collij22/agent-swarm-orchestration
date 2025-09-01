import React, { useState } from 'react';
import { Bot } from 'lucide-react';

type Difficulty = 'easy' | 'medium' | 'hard';

export function PlayPage() {
  const [selectedDifficulty, setSelectedDifficulty] = useState<Difficulty>('medium');
  const [gameStarted, setGameStarted] = useState(false);

  const startGame = () => {
    setGameStarted(true);
    // TODO: Initialize game with selected difficulty
  };

  if (gameStarted) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-gray-800 rounded-lg p-8 text-center">
          <h2 className="text-3xl font-bold mb-4">Game In Progress</h2>
          <p className="text-gray-400">
            Game functionality will be implemented here...
          </p>
          <button
            onClick={() => setGameStarted(false)}
            className="mt-4 px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            End Game
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold text-center mb-8">Single Player Mode</h1>
      
      <div className="bg-gray-800 rounded-lg p-8">
        <h2 className="text-2xl font-bold mb-6 flex items-center">
          <Bot className="w-6 h-6 mr-2 text-blue-400" />
          Select AI Difficulty
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <button
            onClick={() => setSelectedDifficulty('easy')}
            className={`p-4 rounded-lg border-2 transition-all ${
              selectedDifficulty === 'easy'
                ? 'border-green-400 bg-green-900/20'
                : 'border-gray-600 hover:border-gray-500'
            }`}
          >
            <h3 className="text-xl font-bold text-green-400 mb-2">Easy</h3>
            <p className="text-sm text-gray-400">
              AI makes occasional mistakes and uses simpler words
            </p>
          </button>

          <button
            onClick={() => setSelectedDifficulty('medium')}
            className={`p-4 rounded-lg border-2 transition-all ${
              selectedDifficulty === 'medium'
                ? 'border-yellow-400 bg-yellow-900/20'
                : 'border-gray-600 hover:border-gray-500'
            }`}
          >
            <h3 className="text-xl font-bold text-yellow-400 mb-2">Medium</h3>
            <p className="text-sm text-gray-400">
              Balanced AI with good vocabulary and math skills
            </p>
          </button>

          <button
            onClick={() => setSelectedDifficulty('hard')}
            className={`p-4 rounded-lg border-2 transition-all ${
              selectedDifficulty === 'hard'
                ? 'border-red-400 bg-red-900/20'
                : 'border-gray-600 hover:border-gray-500'
            }`}
          >
            <h3 className="text-xl font-bold text-red-400 mb-2">Hard</h3>
            <p className="text-sm text-gray-400">
              Expert AI with extensive vocabulary and perfect math
            </p>
          </button>
        </div>

        <div className="text-center">
          <button
            onClick={startGame}
            className="px-8 py-3 bg-blue-600 text-white text-xl font-bold rounded-lg hover:bg-blue-700 transition-colors"
          >
            Start Game
          </button>
        </div>
      </div>
    </div>
  );
}