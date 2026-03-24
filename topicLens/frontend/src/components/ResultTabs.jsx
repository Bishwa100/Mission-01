import { useState } from 'react'
import ResultCard from './ResultCard'

const TAB_CONFIG = {
  youtube: { label: 'YouTube', icon: '🎥' },
  github: { label: 'GitHub', icon: '🐙' },
  linkedin: { label: 'LinkedIn', icon: '👤' },
  twitter: { label: 'Twitter/X', icon: '🐦' },
  facebook: { label: 'Facebook', icon: '📘' },
  instagram: { label: 'Instagram', icon: '📸' },
  quora: { label: 'Quora', icon: '❓' },
  blogs: { label: 'Blogs', icon: '📝' },
  reddit: { label: 'Reddit', icon: '👥' },
  events: { label: 'Events', icon: '📅' },
}

export default function ResultTabs({ results }) {
  const availableTabs = Object.keys(results).filter(
    key => results[key] && results[key].length > 0
  )

  const [activeTab, setActiveTab] = useState(availableTabs[0] || 'youtube')

  if (availableTabs.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🔍</div>
        <p>No results found. Try a different topic.</p>
      </div>
    )
  }

  const currentResults = results[activeTab] || []

  return (
    <div className="tabs-container">
      <div className="tabs-list">
        {availableTabs.map(tabKey => {
          const config = TAB_CONFIG[tabKey] || { label: tabKey, icon: '📄' }
          const count = results[tabKey]?.length || 0

          return (
            <button
              key={tabKey}
              className={`tab-button ${activeTab === tabKey ? 'active' : ''}`}
              onClick={() => setActiveTab(tabKey)}
            >
              {config.icon} {config.label}
              <span className="tab-count">{count}</span>
            </button>
          )
        })}
      </div>

      <div className="results-grid">
        {currentResults.map((item, index) => (
          <ResultCard key={`${activeTab}-${index}`} item={item} />
        ))}
      </div>
    </div>
  )
}
