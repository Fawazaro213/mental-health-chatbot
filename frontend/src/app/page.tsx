"use client";

import { useState, useEffect, FormEvent, useRef } from 'react';
import { useAuth } from './context/AuthContext';
import { useRouter } from 'next/navigation';

interface ChatMessage {
  sender: "user" | "bot";
  text: string;
}

export default function Home() {
  const { isLoggedIn } = useAuth();
  const router = useRouter();
  
  const [inputValue, setInputValue] = useState("");
  const [chatLog, setChatLog] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // This effect will run once when the component mounts
  useEffect(() => {
    // 1. Protect the route: If not logged in, redirect to login page
    if (!isLoggedIn) {
      router.push('/login');
      return; // Stop execution of the effect
    }

    // 2. Fetch chat history
    const fetchHistory = async () => {
      setIsLoading(true);
      const token = localStorage.getItem('auth_token');
      try {
        const response = await fetch('http://127.0.0.1:5000/api/chat/history', {
          headers: { 'x-access-token': token || '' },
        });
        if (response.ok) {
          const data = await response.json();
          setChatLog(data.history);
        } else {
          console.error("Failed to fetch chat history.");
        }
      } catch (error) {
        console.error("Error fetching chat history:", error);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchHistory();
  }, [isLoggedIn, router]);

  // Auto-scroll to the bottom of the chat log
  useEffect(() => {
    chatContainerRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatLog]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = { sender: "user", text: inputValue };
    // Add user message to log immediately for a responsive feel
    setChatLog(prevLog => [...prevLog, userMessage]);
    setIsLoading(true);
    const currentInput = inputValue;
    setInputValue("");

    try {
      const token = localStorage.getItem('auth_token');
      // 3. Send message with auth token
      const response = await fetch("http://127.0.0.1:5000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-access-token": token || '', // Send token for authentication
        },
        body: JSON.stringify({ message: currentInput }),
      });

      const data = await response.json();
      const botMessage: ChatMessage = { sender: "bot", text: data.response };
      // Add bot's response to the log
      setChatLog(prevLog => [...prevLog, botMessage]);

    } catch (error) {
      const errorMessage: ChatMessage = { sender: "bot", text: "Sorry, something went wrong. Please try again." };
      setChatLog(prevLog => [...prevLog, errorMessage]);
      console.error("Error fetching chat response:", error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // If the user is not logged in, we can render nothing or a loading spinner
  // as the redirect will happen very quickly.
  if (!isLoggedIn) {
    return null; 
  }

  // The JSX for the chat interface remains largely the same
  return (
    <div className="flex flex-col h-[calc(100vh-68px)] bg-gray-900 text-white">
      <main className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="max-w-3xl mx-auto">
          {chatLog.map((message, index) => (
            <div key={index} className={`flex mb-4 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`rounded-lg px-4 py-2 max-w-lg ${message.sender === 'user' ? 'bg-blue-600' : 'bg-gray-700'}`}>
                <p className="text-white">{message.text}</p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start mb-4">
              <div className="rounded-lg px-4 py-2 max-w-lg bg-gray-700">
                <p className="text-white animate-pulse">Bot is typing...</p>
              </div>
            </div>
          )}
          <div ref={chatContainerRef} />
        </div>
      </main>

      <footer className="bg-gray-800 p-4">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto flex items-center">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your message here..."
            className="flex-1 p-2 rounded-l-md bg-gray-700 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="bg-blue-600 text-white px-4 py-2 rounded-r-md hover:bg-blue-700 disabled:bg-gray-500"
            disabled={isLoading || !inputValue.trim()}
          >
            Send
          </button>
        </form>
      </footer>
    </div>
  );
}