import { useState } from 'react'
import { Button, MultiSelect, Search } from '@carbon/react'

function SearchBar({ onSearch, loading, availableFields = [] }) {
  const [value, setValue] = useState('')
  const [selectedFields, setSelectedFields] = useState([])

  const submit = () => {
    if (!loading) onSearch(value, selectedFields)
  }

  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: '1rem', flexWrap: 'wrap' }}>
      <div style={{ flex: 2, minWidth: '240px' }}>
        <Search
          size="lg"
          labelText="Search processes"
          placeholder="Search processes"
          value={value}
          disabled={loading}
          onChange={(e) => setValue(e.target.value)}
          onClear={() => setValue('')}
          onKeyDown={(e) => {
            if (e.key === 'Enter') submit()
          }}
        />
      </div>
      {availableFields.length > 0 && (
        <div style={{ flex: 1, minWidth: '200px' }}>
          <MultiSelect
            id="mandatory-fields-select"
            titleText="Mandatory metadata"
            label="Select fields…"
            items={availableFields}
            itemToString={(item) => item}
            disabled={loading}
            onChange={({ selectedItems }) => setSelectedFields(selectedItems)}
          />
        </div>
      )}
      <Button onClick={submit} disabled={loading}>
        Search
      </Button>
    </div>
  )
}

export default SearchBar
