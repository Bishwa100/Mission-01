export default function ResultCard({ item }) {
  const { title, url, description, thumbnail, source, stars, language, channel, subscribers, score } = item

  return (
    <div className="result-card">
      <a href={url} target="_blank" rel="noopener noreferrer">
        {thumbnail && (
          <img
            src={thumbnail}
            alt={title}
            className="result-thumbnail"
            onError={(e) => {
              e.target.style.display = 'none'
            }}
          />
        )}
        <h3 className="result-title">{title}</h3>
        <p className="result-description">{description}</p>
        <div className="result-meta">
          <span className="result-source">{source}</span>
          <div className="result-stats">
            {stars !== undefined && <span>⭐ {stars.toLocaleString()}</span>}
            {language && <span>{language}</span>}
            {channel && <span>📺 {channel}</span>}
            {subscribers !== undefined && <span>👥 {subscribers.toLocaleString()}</span>}
            {score !== undefined && <span>⬆️ {score}</span>}
          </div>
        </div>
      </a>
    </div>
  )
}
