import React, { useState } from 'react';
import { Users, Plus, Search } from 'lucide-react';

export function MultiplayerPage() {
  const [inviteCode, setInviteCode] = useState('');
  const [showCreateGame, setShowCreateGame] = useState(false);

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold text-center mb-8">Multiplayer</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-2xl font-bold mb-4 flex items-center">
            <Plus className="w-6 h-6 mr-2 text-green-400" />
            Create Game
          </h2>
          <p className="text-gray-400 mb-4">
            Host a new game and invite friends to join
          </p>
          <button
            onClick={() => setShowCreateGame(true)}
            className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            Create New Game
          </button>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-2xl font-bold mb-4 flex items-center">
            <Search className="w-6 h-6 mr-2 text-blue-400" />
            Join Game
          </h2>
          <p className="text-gray-400 mb-4">
            Enter an invite code to join a friend's game
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
              placeholder="Enter code"
              maxLength={6}
              className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
            <button
              onClick={() => console.log('Join game:', inviteCode)}
              disabled={inviteCode.length !== 6}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed"
            >
              Join
            </button>
          </div>
        </div>
      </div>

      <div className="mt-8 bg-gray-800 rounded-lg p-6">
        <h2 className="text-2xl font-bold mb-4 flex items-center">
          <Users className="w-6 h-6 mr-2 text-purple-400" />
          Open Games
        </h2>
        <div className="space-y-2">
          <p className="text-gray-400">No open games available</p>
          {/* TODO: List of available games to join */}
        </div>
      </div>

      {showCreateGame && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-2xl font-bold mb-4">Game Created!</h3>
            <p className="text-gray-400 mb-4">Share this code with friends:</p>
            <div className="text-4xl font-mono text-center text-blue-400 mb-6">
              ABC123
            </div>
            <button
              onClick={() => setShowCreateGame(false)}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Start Game
            </button>
          </div>
        </div>
      )}
    </div>
  );
}