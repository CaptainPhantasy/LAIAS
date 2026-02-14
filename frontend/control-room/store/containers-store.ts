/**
 * Containers Store
 * Manages container list state, filtering, and selection
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type {
  ContainerInfo,
  ContainerFilters,
  ContainerStatus,
} from '../types';

export interface ContainersState {
  // State
  containers: ContainerInfo[];
  isLoading: boolean;
  error: string | null;
  filters: ContainerFilters;
  selectedContainerId: string | null;

  // Actions
  setContainers: (containers: ContainerInfo[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setFilters: (filters: Partial<ContainerFilters>) => void;
  selectContainer: (id: string | null) => void;
  updateContainer: (id: string, updates: Partial<ContainerInfo>) => void;
  removeContainer: (id: string) => void;

  // Selectors (computed values)
  getSelectedContainer: () => ContainerInfo | null;
  getFilteredContainers: () => ContainerInfo[];
  getContainerById: (id: string) => ContainerInfo | null;
  getContainersByStatus: (status: ContainerStatus) => ContainerInfo[];
}

const DEFAULT_FILTERS: ContainerFilters = {
  search: '',
  status: 'all',
  agentId: undefined,
};

const createSelectors = (state: ContainersState) => ({
  getSelectedContainer: () =>
    state.selectedContainerId
      ? state.containers.find((c) => c.container_id === state.selectedContainerId) ?? null
      : null,

  getFilteredContainers: () => {
    let filtered = state.containers;

    // Status filter
    if (state.filters.status !== 'all') {
      filtered = filtered.filter((c) => c.status === state.filters.status);
    }

    // Agent filter
    if (state.filters.agentId) {
      filtered = filtered.filter((c) => c.agent_id === state.filters.agentId);
    }

    // Search filter
    if (state.filters.search) {
      const search = state.filters.search.toLowerCase();
      filtered = filtered.filter(
        (c) =>
          c.name?.toLowerCase().includes(search) ||
          c.agent_id?.toLowerCase().includes(search) ||
          c.agent_name?.toLowerCase().includes(search) ||
          c.container_id?.toLowerCase().includes(search)
      );
    }

    return filtered;
  },

  getContainerById: (id: string) =>
    state.containers.find((c) => c.container_id === id) ?? null,

  getContainersByStatus: (status: ContainerStatus) =>
    state.containers.filter((c) => c.status === status),
});

export const useContainersStore = create<ContainersState>()(
  devtools(
    (set, get) => ({
      // Initial state
      containers: [],
      isLoading: false,
      error: null,
      filters: DEFAULT_FILTERS,
      selectedContainerId: null,

      // Actions
      setContainers: (containers) =>
        set({ containers }, false, 'containers/setContainers'),

      setLoading: (isLoading) =>
        set({ isLoading }, false, 'containers/setLoading'),

      setError: (error) =>
        set({ error }, false, 'containers/setError'),

      setFilters: (filters) =>
        set(
          (state) => ({
            filters: { ...state.filters, ...filters },
          }),
          false,
          'containers/setFilters'
        ),

      selectContainer: (selectedContainerId) =>
        set({ selectedContainerId }, false, 'containers/selectContainer'),

      updateContainer: (id, updates) =>
        set(
          (state) => ({
            containers: state.containers.map((container) =>
              container.container_id === id
                ? { ...container, ...updates }
                : container
            ),
          }),
          false,
          'containers/updateContainer'
        ),

      removeContainer: (id) =>
        set(
          (state) => ({
            containers: state.containers.filter(
              (container) => container.container_id !== id
            ),
            selectedContainerId:
              state.selectedContainerId === id ? null : state.selectedContainerId,
          }),
          false,
          'containers/removeContainer'
        ),

      // Selectors
      ...createSelectors(get() as ContainersState),
    }),
    { name: 'ContainersStore' }
  )
);

// Selector hooks for external use
export const useSelectedContainer = () =>
  useContainersStore((state) => state.getSelectedContainer());

export const useFilteredContainers = () =>
  useContainersStore((state) => state.getFilteredContainers());

export const useContainerById = (id: string) =>
  useContainersStore((state) => state.getContainerById(id));

export const useContainersByStatus = (status: ContainerStatus) =>
  useContainersStore((state) => state.getContainersByStatus(status));
