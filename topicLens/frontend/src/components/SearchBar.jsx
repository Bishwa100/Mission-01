import { useState } from 'react'

export default function SearchBar({ onSearch, isLoading }) {
  const [topic, setTopic] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (topic.trim() && !isLoading) {
      onSearch(topic.trim())
    }
  }

  return (
    <form onSubmit={handleSubmit} className="search-container">
      <input
        type="text"
        className="search-input"
        placeholder="Enter any topic... (e.g., Machine Learning, Yoga, Blockchain)"
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        disabled={isLoading}
      />
      <button
        type="submit"
        className="search-button"
        disabled={isLoading || !topic.trim()}
      >
        {isLoading ? 'Searching...' : 'Explore'}
      </button>
    </form>
  )
}
