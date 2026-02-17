import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  AgentFormData,
  GenerationState,
  ValidationStatus,
  CodeTab,
} from '@/types';
import { DEFAULT_AGENT_FORM } from '@/types';

// ============================================================================
// Types
// ============================================================================

interface GeneratedCode {
  agentId: string;
  flowCode: string;
  agentsYaml: string;
  requirements: string;
  stateCode: string;
}

interface BuilderState {
  // Form data
  formData: AgentFormData;

  // Generation state
  generationState: GenerationState;
  generatedCode: GeneratedCode | null;
  generationError: string | null;

  // Code editor
  activeTab: CodeTab;
  codeFiles: Record<CodeTab, { content: string; isDirty: boolean }>;

  // Validation
  validationStatus: ValidationStatus | null;

  // UI state
  activeSection: string;
  isAdvancedOpen: boolean;

  // Actions - Form
  setFormData: (data: Partial<AgentFormData>) => void;
  resetForm: () => void;

  // Actions - Generation
  setGenerationState: (state: GenerationState) => void;
  setGeneratedCode: (code: GeneratedCode | null) => void;
  setGenerationError: (error: string | null) => void;
  resetGeneration: () => void;

  // Actions - Code Editor
  setActiveTab: (tab: CodeTab) => void;
  updateCodeContent: (tab: CodeTab, content: string) => void;
  resetCodeFile: (tab: CodeTab) => void;
  resetAllCode: () => void;

  // Actions - Validation
  setValidationStatus: (status: ValidationStatus | null) => void;

  // Actions - UI
  setActiveSection: (section: string) => void;
  toggleAdvanced: () => void;
}

// ============================================================================
// Initial State
// ============================================================================

const initialCodeFiles: Record<CodeTab, { content: string; isDirty: boolean }> = {
  'flow.py': { content: '', isDirty: false },
  'agents.yaml': { content: '', isDirty: false },
  'requirements.txt': { content: '', isDirty: false },
  'state.py': { content: '', isDirty: false },
};

// ============================================================================
// Store
// ============================================================================

export const useBuilderStore = create<BuilderState>()(
  persist(
    (set, get) => ({
      // Initial state
      formData: DEFAULT_AGENT_FORM,
      generationState: 'idle',
      generatedCode: null,
      generationError: null,
      activeTab: 'flow.py',
      codeFiles: initialCodeFiles,
      validationStatus: null,
      activeSection: 'description',
      isAdvancedOpen: false,

      // Form actions
      setFormData: (data) =>
        set((state) => ({
          formData: { ...state.formData, ...data },
        })),

      resetForm: () =>
        set({
          formData: DEFAULT_AGENT_FORM,
          generationState: 'idle',
          generatedCode: null,
          generationError: null,
          validationStatus: null,
          codeFiles: initialCodeFiles,
        }),

      // Generation actions
      setGenerationState: (state) => set({ generationState: state }),

      setGeneratedCode: (code) => {
        if (code) {
          set({
            generatedCode: code,
            codeFiles: {
              'flow.py': { content: code.flowCode, isDirty: false },
              'agents.yaml': { content: code.agentsYaml, isDirty: false },
              'requirements.txt': { content: code.requirements, isDirty: false },
              'state.py': { content: code.stateCode, isDirty: false },
            },
          });
        } else {
          set({
            generatedCode: null,
            codeFiles: initialCodeFiles,
          });
        }
      },

      setGenerationError: (error) => set({ generationError: error }),

      resetGeneration: () =>
        set({
          generationState: 'idle',
          generatedCode: null,
          generationError: null,
          validationStatus: null,
          codeFiles: initialCodeFiles,
        }),

      // Code editor actions
      setActiveTab: (tab) => set({ activeTab: tab }),

      updateCodeContent: (tab, content) =>
        set((state) => ({
          codeFiles: {
            ...state.codeFiles,
            [tab]: { content, isDirty: true },
          },
        })),

      resetCodeFile: (tab) => {
        const { generatedCode } = get();
        const originalContent =
          tab === 'flow.py'
            ? generatedCode?.flowCode || ''
            : tab === 'agents.yaml'
              ? generatedCode?.agentsYaml || ''
              : tab === 'state.py'
                ? generatedCode?.stateCode || ''
                : generatedCode?.requirements || '';

        set((state) => ({
          codeFiles: {
            ...state.codeFiles,
            [tab]: { content: originalContent, isDirty: false },
          },
        }));
      },

      resetAllCode: () => {
        const { generatedCode } = get();
        set({
          codeFiles: {
            'flow.py': { content: generatedCode?.flowCode || '', isDirty: false },
            'agents.yaml': { content: generatedCode?.agentsYaml || '', isDirty: false },
            'requirements.txt': { content: generatedCode?.requirements || '', isDirty: false },
            'state.py': { content: generatedCode?.stateCode || '', isDirty: false },
          },
        });
      },

      // Validation actions
      setValidationStatus: (status) => set({ validationStatus: status }),

      // UI actions
      setActiveSection: (section) => set({ activeSection: section }),

      toggleAdvanced: () =>
        set((state) => ({ isAdvancedOpen: !state.isAdvancedOpen })),
    }),
    {
      name: 'laias-studio-builder',
      partialize: (state) => ({
        formData: state.formData,
        isAdvancedOpen: state.isAdvancedOpen,
      }),
    }
  )
);

// ============================================================================
// Selectors
// ============================================================================

export const selectFormData = (state: BuilderState) => state.formData;
export const selectGenerationState = (state: BuilderState) => state.generationState;
export const selectGeneratedCode = (state: BuilderState) => state.generatedCode;
export const selectValidationStatus = (state: BuilderState) => state.validationStatus;
export const selectActiveTab = (state: BuilderState) => state.activeTab;
export const selectCodeFiles = (state: BuilderState) => state.codeFiles;
export const selectActiveSection = (state: BuilderState) => state.activeSection;

// ============================================================================
// Hooks
// ============================================================================

export function useFormActions() {
  const setFormData = useBuilderStore((s) => s.setFormData);
  const resetForm = useBuilderStore((s) => s.resetForm);
  return { setFormData, resetForm };
}

export function useGenerationActions() {
  const setGenerationState = useBuilderStore((s) => s.setGenerationState);
  const setGeneratedCode = useBuilderStore((s) => s.setGeneratedCode);
  const setGenerationError = useBuilderStore((s) => s.setGenerationError);
  const resetGeneration = useBuilderStore((s) => s.resetGeneration);
  return { setGenerationState, setGeneratedCode, setGenerationError, resetGeneration };
}

export function useCodeEditorActions() {
  const setActiveTab = useBuilderStore((s) => s.setActiveTab);
  const updateCodeContent = useBuilderStore((s) => s.updateCodeContent);
  const resetCodeFile = useBuilderStore((s) => s.resetCodeFile);
  const resetAllCode = useBuilderStore((s) => s.resetAllCode);
  return { setActiveTab, updateCodeContent, resetCodeFile, resetAllCode };
}
