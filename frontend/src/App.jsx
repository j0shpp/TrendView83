import { useState, useEffect } from 'react'
import { RefreshCw, TrendingUp, TrendingDown, Minus, ExternalLink, Loader2, AlertTriangle } from 'lucide-react'

const API_BASE = '/api'

function SentimentBadge({ sentiment, score }) {
  const config = {
    bullish: { class: 'bg-bullish-100 text-bullish-600', icon: <TrendingUp className="w-3 h-3" />, label: 'Bullish' },
    bearish: { class: 'bg-bearish-100 text-bearish-600', icon: <TrendingDown className="w-3 h-3" />, label: 'Bearish' },
    neutral: { class: 'bg-neutral-100 text-neutral-600', icon: <Minus className="w-3 h-3" />, label: 'Neutral' },
  }
  const c = config[sentiment] || config.neutral
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${c.class}`}>
      {c.icon} {c.label} <span className="font-mono">({score > 0 ? '+' : ''}{score.toFixed(2)})</span>
    </span>
  )
}

function ChangeCell({ change, changePercent }) {
  const isPositive = change >= 0
  return (
    <span className={`font-mono font-medium ${isPositive ? 'text-bullish-600' : 'text-bearish-600'}`}>
      {isPositive ? '+' : ''}{change.toFixed(2)} ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
    </span>
  )
}

function MentionRow({ mention }) {
  const sourceIcon = mention.source === 'reddit' ? '📱' : '📰'
  const sentimentColor = {
    bullish: 'text-bullish-600',
    bearish: 'text-bearish-600',
    neutral: 'text-neutral-600',
  }[mention.sentiment]

  return (
    <tr className="border-t border-neutral-100 hover:bg-neutral-50">
      <td className="px-3 py-2 text-xs text-neutral-500">{sourceIcon} {mention.source}</td>
      <td className="px-3 py-2 text-xs font-medium">{mention.title}</td>
      <td className="px-3 py-2 text-xs text-neutral-600 max-w-xs truncate">{mention.excerpt}</td>
      <td className="px-3 py-2 text-xs font-medium {sentimentColor}">{mention.sentiment}</td>
      <td className="px-3 py-2 text-xs text-neutral-400 font-mono">{new Date(mention.timestamp).toLocaleString()}</td>
      <td className="px-3 py-2">
        <a href={mention.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline flex items-center gap-1">
          <ExternalLink className="w-3 h-3" /> Source
        </a>
      </td>
    </tr>
  )
}

function TickerDetail({ ticker, onClose }) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchDetail() {
      try {
        const res = await fetch(`${API_BASE}/trending/${ticker}`)
        const data = await res.json()
        setDetail(data)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchDetail()
  }, [ticker])

  if (loading) return <div className="p-8 text-center">Loading...</div>
  if (!detail || detail.error) return <div className="p-8 text-center text-red-600">Not found</div>

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-3xl w-full max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-bold">{detail.ticker} Details</h2>
          <button onClick={onClose} className="text-neutral-400 hover:text-neutral-600">✕</button>
        </div>
        <div className="p-4">
          {detail.snapshot && (
            <div className="grid grid-cols-2 gap-4 mb-6 p-4 bg-neutral-50 rounded-lg">
              <div>
                <p className="text-sm text-neutral-500">Price</p>
                <p className="text-2xl font-bold font-mono">${detail.snapshot.price.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-neutral-500">Change</p>
                <p className={`text-xl font-bold font-mono ${detail.snapshot.change >= 0 ? 'text-bullish-600' : 'text-bearish-600'}`}>
                  {detail.snapshot.change >= 0 ? '+' : ''}{detail.snapshot.change.toFixed(2)} ({detail.snapshot.changePercent >= 0 ? '+' : ''}{detail.snapshot.changePercent.toFixed(2)}%)
                </p>
              </div>
              <div>
                <p className="text-sm text-neutral-500">Volume</p>
                <p className="text-xl font-bold font-mono">{detail.snapshot.volume.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm text-neutral-500">Market Cap</p>
                <p className="text-xl font-bold font-mono">{detail.snapshot.market_cap ? '$' + (detail.snapshot.market_cap / 1e9).toFixed(2) + 'B' : 'N/A'}</p>
              </div>
            </div>
          )}

          <div>
            <h3 className="font-semibold mb-3">Recent Mentions ({detail.mentions.length})</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-neutral-500 uppercase tracking-wider bg-neutral-50">
                    <th className="px-3 py-2">Source</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Excerpt</th>
                    <th className="px-3 py-2">Sentiment</th>
                    <th className="px-3 py-2">Time</th>
                    <th className="px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {detail.mentions.map((m, i) => <MentionRow key={i} mention={m} />)}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [trending, setTrending] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [totalMentions, setTotalMentions] = useState(0)
  const [selectedTicker, setSelectedTicker] = useState(null)
  const [error, setError] = useState(null)

  async function fetchTrending() {
    try {
      setError(null)
      const res = await fetch(`${API_BASE}/trending`)
      if (!res.ok) throw new Error('Failed to fetch')
      const data = await res.json()
      setTrending(data.trending)
      setLastUpdated(new Date(data.last_updated))
      setTotalMentions(data.total_mentions)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTrending()
    const interval = setInterval(fetchTrending, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <header className="bg-white border-b border-neutral-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-bullish-600 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-neutral-900">TrendView83</h1>
              <p className="text-xs text-neutral-500">Trending US stocks from social sentiment</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm text-neutral-600">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-bullish-500 rounded-full" />
              Live • Updated {lastUpdated ? lastUpdated.toLocaleTimeString() : '—'}
            </span>
            <button
              onClick={fetchTrending}
              disabled={loading}
              className="flex items-center gap-2 px-3 py-1.5 border border-neutral-300 rounded-lg hover:bg-neutral-50 disabled:opacity-50 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2 flex items-center justify-between">
          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mr-2" />
          <span className="text-sm text-red-700 flex-1">Failed to load: {error}</span>
          <button onClick={fetchTrending} className="text-sm text-red-600 hover:underline">Retry</button>
        </div>
      )}

      {/* Stats bar */}
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-6 text-sm text-neutral-600 border-b border-neutral-200 bg-white">
        <span className="font-medium text-neutral-900">{trending.length} trending tickers</span>
        <span>{totalMentions.toLocaleString()} total mentions</span>
        <span className="text-neutral-400">Auto-refresh: 5min</span>
        <span className="text-neutral-400 font-mono">Sources: Reddit + Financial News RSS</span>
      </div>

      {/* Table */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {loading && trending.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="w-8 h-8 animate-spin text-bullish-600" />
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-neutral-200 bg-white shadow-sm">
            <table className="w-full">
              <thead>
                <tr className="text-left text-xs text-neutral-500 uppercase tracking-wider bg-neutral-50 border-b border-neutral-200">
                  <th className="px-4 py-3 w-12">#</th>
                  <th className="px-4 py-3 w-24 font-mono">Ticker</th>
                  <th className="px-4 py-3">Mentions</th>
                  <th className="px-4 py-3">Sentiment</th>
                  <th className="px-4 py-3 w-48">Price</th>
                  <th className="px-4 py-3 w-40">Change</th>
                  <th className="px-4 py-3 w-32">Volume</th>
                  <th className="px-4 py-3 w-28">Market Cap</th>
                  <th className="px-4 py-3 w-12"></th>
                </tr>
              </thead>
              <tbody>
                {trending.map((t) => (
                  <tr
                    key={t.ticker}
                    className="border-t border-neutral-100 hover:bg-neutral-50 cursor-pointer transition-colors"
                    onClick={() => setSelectedTicker(t.ticker)}
                  >
                    <td className="px-4 py-3 text-sm font-medium text-neutral-600">{t.rank}</td>
                    <td className="px-4 py-3 font-mono font-semibold text-neutral-900">{t.ticker}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-neutral-100 text-neutral-700 text-sm font-medium">
                        {t.mention_count}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <SentimentBadge sentiment={t.sentiment} score={t.sentiment_score} />
                    </td>
                    <td className="px-4 py-3">
                      {t.snapshot ? (
                        <span className="font-mono font-medium text-lg">${t.snapshot.price.toFixed(2)}</span>
                      ) : (
                        <span className="text-neutral-400 text-sm">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {t.snapshot ? (
                        <ChangeCell change={t.snapshot.change} changePercent={t.snapshot.change_percent} />
                      ) : (
                        <span className="text-neutral-400 text-sm">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {t.snapshot ? (
                        <span className="font-mono text-sm text-neutral-600">{t.snapshot.volume.toLocaleString()}</span>
                      ) : (
                        <span className="text-neutral-400 text-sm">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {t.snapshot?.market_cap ? (
                        <span className="font-mono text-sm text-neutral-600">${(t.snapshot.market_cap / 1e9).toFixed(1)}B</span>
                      ) : (
                        <span className="text-neutral-400 text-sm">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-neutral-400 hover:text-neutral-600">→</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {trending.length === 0 && !loading && (
          <div className="text-center py-12 text-neutral-500">
            <AlertTriangle className="w-12 h-12 mx-auto mb-3 text-neutral-300" />
            <p>No trending tickers found. Try refreshing.</p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-neutral-200 bg-white mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-4 text-xs text-neutral-500 text-center">
          Data from Reddit (public API) & Financial News RSS • Prices via yfinance • Not financial advice
        </div>
      </footer>

      {selectedTicker && (
        <TickerDetail ticker={selectedTicker} onClose={() => setSelectedTicker(null)} />
      )}
    </div>
  )
}