import { useEffect, useState } from 'react'
import {
  Header,
  HeaderName,
  HeaderNavigation,
  HeaderMenuItem,
  InlineLoading,
  InlineNotification,
} from '@carbon/react'
import SearchBar from './components/SearchBar'
import ResultsTable from './components/ResultsTable'
import GlossaryModal from './components/GlossaryModal'
import DiagramDownload from './components/DiagramDownload'
import { fetchMetadataFields, searchProcesses } from './api/client'

function App() {
  const [showGlossary, setShowGlossary] = useState(false)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedProcessId, setSelectedProcessId] = useState(null)
  const [availableFields, setAvailableFields] = useState([])

  useEffect(() => {
    fetchMetadataFields()
      .then(setAvailableFields)
      .catch(() => {/* non-fatal — dropdown simply won't appear */})
  }, [])

  const handleSearch = async (query, mandatoryFields) => {
    setLoading(true)
    setError(null)
    setSelectedProcessId(null)
    try {
      const data = await searchProcesses(query, mandatoryFields)
      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Header aria-label="IBM Blueworks Live">
        <HeaderName href="#" prefix="IBM">
          Blueworks Live
        </HeaderName>
        <HeaderNavigation aria-label="Main navigation">
          <HeaderMenuItem
            href="#"
            onClick={(e) => {
              e.preventDefault()
              setShowGlossary(true)
            }}
          >
            Glossary
          </HeaderMenuItem>
        </HeaderNavigation>
      </Header>
      <main className="cds--content" style={{ paddingTop: '3rem' }}>
        {error && (
          <InlineNotification
            kind="error"
            title="Search failed"
            subtitle={error}
            onCloseButtonClick={() => setError(null)}
          />
        )}
        <SearchBar onSearch={handleSearch} loading={loading} availableFields={availableFields} />
        {loading && <InlineLoading description="Searching..." />}
        <ResultsTable rows={results} onRowSelect={setSelectedProcessId} />
        {results.length > 0 && <p>{results.length} result(s) found</p>}
        <DiagramDownload processId={selectedProcessId} />
        <GlossaryModal open={showGlossary} onClose={() => setShowGlossary(false)} />
      </main>
    </>
  )
}

export default App
