"use client";

import Link from 'next/link';
import { useAuth } from '../context/AuthContext'; // Import our custom hook

const Navbar = () => {
  const { isLoggedIn, logout } = useAuth(); // Get auth state and logout function

  return (
    <nav className="bg-gray-800 shadow-md p-4">
      <div className="max-w-5xl mx-auto flex justify-between items-center">
        <Link href="/" className="text-xl font-bold text-white">
          AI Mental Health Chatbot
        </Link>
        <div className="flex space-x-4 items-center">
          {isLoggedIn ? (
            // If user is logged in, show a Logout button
           <>
          <Link href="/journal" className="text-gray-300 hover:text-white">
            Journal
          </Link>
          <button
            onClick={logout}
            className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
          >
            Logout
          </button>
        </>
          ) : (
            // If user is not logged in, show Login and Sign Up links
            <>
              <Link href="/login" className="text-gray-300 hover:text-white">
                Login
              </Link>
              <Link href="/signup" className="text-gray-300 hover:text-white">
                Sign Up
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;