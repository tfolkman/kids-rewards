import React, { useState, useRef, useEffect } from 'react';
import { TextInput, List, Paper, Box, useMantineTheme, Button, ActionIcon } from '@mantine/core';
import { IconSearch, IconX } from '@tabler/icons-react';
import * as api from '../services/api';

interface SearchBarProps {
  items: api.StoreItem[];
  onSearch: (results: api.StoreItem[]) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ items, onSearch }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<api.StoreItem[]>([]);
  const [showResults, setShowResults] = useState(false);
  const theme = useMantineTheme();
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!searchTerm) {
      onSearch(items);
      setShowResults(false);
    }
  }, [items, onSearch, searchTerm]);

  const handleSearch = (term: string) => {
    setSearchTerm(term);
    const results = items.filter(item =>
      item.name.toLowerCase().includes(term.toLowerCase())
    );
    setSearchResults(results);
    onSearch(results);
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    setSearchResults(items);
    onSearch(items);
    setShowResults(false);
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      setShowResults(false);
      handleBlur();
    }
  };

  const handleBlur = () => {
    if (searchTerm.length > 0) {
      handleSearch(searchTerm);
      setShowResults(true);
    } else {
      setSearchResults(items);
      onSearch(items);
      setShowResults(false);
    }
  };

  return (
    <Box>
      <TextInput
        placeholder="Search for items"
        value={searchTerm}
        onChange={(event) => handleSearch(event.currentTarget.value)}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        radius="md"
        size="md"
        ref={searchInputRef}
        leftSection={<IconSearch size={16} />}
        rightSection={searchTerm && (
          <ActionIcon
            color="gray"
            size="sm"
            radius="xl"
            onClick={handleClearSearch}
            aria-label="Clear search"
          >
            <IconX size={16} />
          </ActionIcon>
        )}
      />
      {showResults && searchResults.length > 0 && (
        <Paper shadow="sm" radius="md" p="md" mt="xs" withBorder>
          <List
            spacing="xs"
            size="sm"
            center
            listStyleType="none"
          >
            {searchResults.map((item) => (
              <List.Item key={item.id}>{item.name}</List.Item>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
};

export default SearchBar;