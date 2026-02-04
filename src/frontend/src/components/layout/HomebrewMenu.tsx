import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Menu,
  MenuTrigger,
  MenuPopover,
  MenuList,
  MenuItem,
  Spinner,
} from '@fluentui/react-components';
import { homebrewService } from '../../services/homebrewService';
import type { HomebrewTreeNode } from '../../types/homebrew';

interface HomebrewMenuProps {
  triggerClassName: string;
}

export default function HomebrewMenu({ triggerClassName }: HomebrewMenuProps) {
  const navigate = useNavigate();
  const [tree, setTree] = useState<HomebrewTreeNode[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const fetchTree = useCallback(async () => {
    if (tree !== null) return;
    setLoading(true);
    setError(false);
    try {
      const data = await homebrewService.getTree();
      setTree(data);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [tree]);

  const handleOpenChange = useCallback(
    (_: unknown, data: { open: boolean }) => {
      if (data.open) {
        fetchTree();
      }
    },
    [fetchTree]
  );

  return (
    <Menu openOnHover onOpenChange={handleOpenChange}>
      <MenuTrigger disableButtonEnhancement>
        <span className={triggerClassName}>Homebrew</span>
      </MenuTrigger>
      <MenuPopover>
        <MenuList>
          {loading && (
            <MenuItem disabled>
              <Spinner size="tiny" label="Loading..." />
            </MenuItem>
          )}
          {error && (
            <MenuItem disabled>Failed to load</MenuItem>
          )}
          {tree && tree.length === 0 && (
            <MenuItem disabled>No documents found</MenuItem>
          )}
          {tree && tree.map((node) => (
            <TreeNodeMenuItem
              key={node.path}
              node={node}
              onNavigate={(path) => navigate(`/homebrew/${path}`)}
            />
          ))}
        </MenuList>
      </MenuPopover>
    </Menu>
  );
}

function TreeNodeMenuItem({
  node,
  onNavigate,
}: {
  node: HomebrewTreeNode;
  onNavigate: (path: string) => void;
}) {
  if (node.type === 'file') {
    return (
      <MenuItem onClick={() => onNavigate(node.path)}>
        {node.name}
      </MenuItem>
    );
  }

  return (
    <Menu>
      <MenuTrigger disableButtonEnhancement>
        <MenuItem>{node.name}</MenuItem>
      </MenuTrigger>
      <MenuPopover>
        <MenuList>
          {node.children?.map((child) => (
            <TreeNodeMenuItem
              key={child.path}
              node={child}
              onNavigate={onNavigate}
            />
          ))}
        </MenuList>
      </MenuPopover>
    </Menu>
  );
}
