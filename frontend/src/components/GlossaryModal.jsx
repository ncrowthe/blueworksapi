import { useEffect, useState } from 'react'
import {
  DataTable,
  DataTableSkeleton,
  InlineNotification,
  Modal,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeader,
  TableRow,
} from '@carbon/react'
import { fetchGlossary } from '../api/client'

const headers = [
  { key: 'name', header: 'Name' },
  { key: 'category', header: 'Category' },
  { key: 'addedBy', header: 'Added By' },
]

// Mirrors json_to_table(): data is a list, or a dict whose first list value holds the records
function toRows(data) {
  let records = []
  if (Array.isArray(data)) {
    records = data
  } else if (data && typeof data === 'object') {
    records = Object.values(data).find(Array.isArray) || []
  }
  return records.map((rec, index) => ({
    id: String(index),
    name: rec?.name ?? '',
    category: rec?.category ?? '',
    addedBy: rec?.['added-by-user'] ?? '',
  }))
}

function GlossaryModal({ open, onClose }) {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!open) return undefined
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchGlossary()
      .then((data) => {
        if (!cancelled) setRows(toRows(data))
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [open])

  return (
    <Modal
      open={open}
      onRequestClose={onClose}
      modalHeading="Glossary"
      passiveModal
      size="lg"
    >
      {loading && (
        <DataTableSkeleton
          headers={headers}
          columnCount={headers.length}
          rowCount={5}
          showHeader={false}
          showToolbar={false}
        />
      )}
      {!loading && error && (
        <InlineNotification
          kind="error"
          title="Failed to load glossary"
          subtitle={error}
          hideCloseButton
        />
      )}
      {!loading && !error && (
        <DataTable rows={rows} headers={headers} useZebraStyles>
          {({
            rows: tableRows,
            headers: tableHeaders,
            getTableProps,
            getHeaderProps,
            getRowProps,
          }) => (
            <TableContainer>
              <Table {...getTableProps()}>
                <TableHead>
                  <TableRow>
                    {tableHeaders.map((header) => {
                      const { key, ...headerProps } = getHeaderProps({ header })
                      return (
                        <TableHeader key={key} {...headerProps}>
                          {header.header}
                        </TableHeader>
                      )
                    })}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {tableRows.map((row) => {
                    const { key, ...rowProps } = getRowProps({ row })
                    return (
                      <TableRow key={key} {...rowProps}>
                        {row.cells.map((cell) => (
                          <TableCell key={cell.id}>{cell.value}</TableCell>
                        ))}
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DataTable>
      )}
    </Modal>
  )
}

export default GlossaryModal
