import React from 'react';
import { Table, Card, Text, Badge, Group, Stack, Box, useMatches } from '@mantine/core';

interface ResponsiveTableProps {
  data: any[];
  columns: {
    key: string;
    label: string;
    render?: (value: any, row: any) => React.ReactNode;
    align?: 'left' | 'center' | 'right';
  }[];
  cardRender?: (row: any) => React.ReactNode;
  className?: string;
}

export const ResponsiveTable: React.FC<ResponsiveTableProps> = ({ 
  data, 
  columns, 
  cardRender,
  className = ''
}) => {
  const isMobile = useMatches({
    base: true,
    sm: false,
  });

  if (isMobile) {
    // Mobile card view
    return (
      <Stack gap="md" className={className}>
        {data.map((row, index) => (
          <Card 
            key={index} 
            shadow="sm" 
            p="md" 
            radius="md" 
            withBorder
            className="fade-in card-hover"
          >
            {cardRender ? (
              cardRender(row)
            ) : (
              <Stack gap="xs">
                {columns.map((col) => (
                  <Group key={col.key} justify="space-between">
                    <Text size="sm" c="dimmed">{col.label}:</Text>
                    <Box>
                      {col.render ? col.render(row[col.key], row) : row[col.key]}
                    </Box>
                  </Group>
                ))}
              </Stack>
            )}
          </Card>
        ))}
      </Stack>
    );
  }

  // Desktop table view
  return (
    <Table 
      striped 
      highlightOnHover 
      withTableBorder 
      withColumnBorders 
      verticalSpacing="sm" 
      horizontalSpacing="md"
      className={className}
    >
      <Table.Thead>
        <Table.Tr>
          {columns.map((col) => (
            <Table.Th key={col.key} ta={col.align || 'left'}>
              {col.label}
            </Table.Th>
          ))}
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {data.map((row, index) => (
          <Table.Tr key={index}>
            {columns.map((col) => (
              <Table.Td key={col.key} ta={col.align || 'left'}>
                {col.render ? col.render(row[col.key], row) : row[col.key]}
              </Table.Td>
            ))}
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  );
};

export default ResponsiveTable;