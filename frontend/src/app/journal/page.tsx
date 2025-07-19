"use client";

import { useState, useEffect, FormEvent } from 'react';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/navigation';

interface JournalEntry {
  id: number;
  content: string;
  date_posted: string;
}

export default function JournalPage() {
  const { isLoggedIn } = useAuth();
  const router = useRouter();
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [newEntry, setNewEntry] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // This effect handles fetching the user's journal entries
  useEffect(() => {
    // If the user is not logged in, redirect them to the login page
    if (!isLoggedIn) {
      router.push('/login');
      return;
    }

    const fetchEntries = async () => {
      setIsLoading(true);
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setError("Authentication token not found. Please log in again.");
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch('http://127.0.0.1:5000/api/journal/entries', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'x-access-token': token, // Send the token for authentication
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch journal entries.');
        }

        const data = await response.json();
        setEntries(data.entries);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An unknown error occurred.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchEntries();
  }, [isLoggedIn, router]);

  // This function handles submitting a new journal entry
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!newEntry.trim()) return;

    const token = localStorage.getItem('auth_token');
    try {
      const response = await fetch('http://127.0.0.1:5000/api/journal/entries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-access-token': token || '',
        },
        body: JSON.stringify({ content: newEntry }),
      });

      if (response.ok) {
        setNewEntry(''); // Clear the textarea
        // Re-fetch entries to show the new one
        const updatedEntriesRes = await fetch('http://127.0.0.1:5000/api/journal/entries', { headers: { 'x-access-token': token || '' } });
        const updatedData = await updatedEntriesRes.json();
        setEntries(updatedData.entries);
      } else {
        throw new Error('Failed to submit new entry.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred.");
    }
  };
  
  // Don't render anything if we are redirecting
  if (!isLoggedIn) {
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-6 text-white">
      <h1 className="text-3xl font-bold mb-6">Your Personal Journal</h1>
      
      {/* Form to create a new entry */}
      <form onSubmit={handleSubmit} className="mb-8">
        <textarea
          value={newEntry}
          onChange={(e) => setNewEntry(e.target.value)}
          placeholder="Write your thoughts here..."
          className="w-full h-32 p-3 bg-gray-800 border border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button type="submit" className="mt-2 px-4 py-2 font-bold text-white bg-blue-600 rounded-md hover:bg-blue-700">
          Submit Entry
        </button>
      </form>
      
      {/* Display existing entries */}
      <h2 className="text-2xl font-bold mb-4">Past Entries</h2>
      {isLoading ? (
        <p>Loading entries...</p>
      ) : error ? (
        <p className="text-red-500">{error}</p>
      ) : (
        <div className="space-y-4">
          {entries.length > 0 ? (
            entries.map((entry) => (
              <div key={entry.id} className="bg-gray-800 p-4 rounded-lg shadow">
                <p className="text-gray-300">{entry.content}</p>
                <p className="text-xs text-gray-500 mt-2 text-right">{new Date(entry.date_posted + 'Z').toLocaleString()}</p>
              </div>
            ))
          ) : (
            <p>You have no journal entries yet.</p>
          )}
        </div>
      )}
    </div>
  );
}
