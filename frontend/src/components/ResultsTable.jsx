import {
  DataTable,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeader,
  TableRow,
  TableSelectRow,
  Tag,
} from '@carbon/react'

const headers = [
  { key: 'name', header: 'Name' },
  { key: 'type', header: 'Type' },
  { key: 'space', header: 'Space' },
  { key: 'activities', header: 'Activities' },
  { key: 'compliance', header: 'Compliance' },
]

function ResultsTable({ rows, onRowSelect }) {
  if (!rows || rows.length === 0) {
    return <p>No results. Enter a search term above.</p>
  }

  return (
    <DataTable rows={rows} headers={headers} radio>
      {({
        rows: tableRows,
        headers: tableHeaders,
        getTableProps,
        getHeaderProps,
        getRowProps,
        getSelectionProps,
      }) => (
        <TableContainer title="Search results">
          <Table {...getTableProps()}>
            <TableHead>
              <TableRow>
                <th scope="col" />
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
                const { onSelect, ...selectionProps } = getSelectionProps({ row })
                return (
                  <TableRow key={key} {...rowProps}>
                    <TableSelectRow
                      {...selectionProps}
                      onSelect={(e) => {
                        onSelect(e)
                        onRowSelect(row.id)
                      }}
                    />
                    {row.cells.map((cell) => (
                      <TableCell key={cell.id}>
                        {cell.info.header === 'compliance' ? (
                          <Tag
                            type={cell.value === 'Compliant' ? 'green' : 'red'}
                          >
                            {cell.value}
                          </Tag>
                        ) : (
                          cell.value
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </DataTable>
  )
}

export default ResultsTable
