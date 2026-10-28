import { useState } from 'react'
import { Button, InlineLoading, InlineNotification } from '@carbon/react'
import { Download } from '@carbon/icons-react'
import { downloadDiagram } from '../api/client'

function DiagramDownload({ processId }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleClick = async () => {
    setLoading(true)
    setError(null)
    try {
      await downloadDiagram(processId)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {error && (
        <InlineNotification
          kind="error"
          title="Download failed"
          subtitle={error}
          onCloseButtonClick={() => setError(null)}
        />
      )}
      <Button
        renderIcon={Download}
        disabled={!processId || loading}
        onClick={handleClick}
      >
        Download Diagram
      </Button>
      {loading && <InlineLoading description="Downloading..." />}
    </div>
  )
}

export default DiagramDownload
