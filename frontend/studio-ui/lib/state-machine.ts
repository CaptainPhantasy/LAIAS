/**
 * Interaction State Machine Implementation
 * Per Blueprint Section B.2
 */

// ============================================================================
// Types
// ============================================================================

export type InteractionState = 'idle' | 'focused' | 'active' | 'disabled';

export type AsyncState = 'ready' | 'loading' | 'success' | 'error';

export interface StateMachineConfig<T extends string> {
  initial: T;
  states: Record<T, { on?: Record<string, T> }>;
}

export interface StateMachine<T extends string> {
  state: T;
  transition: (event: string) => void;
  is: (state: T) => boolean;
  matches: (...states: T[]) => boolean;
}

// ============================================================================
// Interaction State Machine
// ============================================================================

export const interactionStates = {
  idle: {
    on: {
      FOCUS: 'focused',
      DISABLE: 'disabled',
    },
  },
  focused: {
    on: {
      BLUR: 'idle',
      ACTIVATE: 'active',
      DISABLE: 'disabled',
    },
  },
  active: {
    on: {
      COMPLETE: 'idle',
      CANCEL: 'idle',
      DISABLE: 'disabled',
    },
  },
  disabled: {
    on: {
      ENABLE: 'idle',
    },
  },
} as const satisfies StateMachineConfig<InteractionState>['states'];

// ============================================================================
// Async State Machine
// ============================================================================

export const asyncStates = {
  ready: {
    on: {
      START: 'loading',
    },
  },
  loading: {
    on: {
      SUCCESS: 'success',
      ERROR: 'error',
    },
  },
  success: {
    on: {
      RESET: 'ready',
      START: 'loading',
    },
  },
  error: {
    on: {
      RETRY: 'loading',
      RESET: 'ready',
    },
  },
} as const satisfies StateMachineConfig<AsyncState>['states'];

// ============================================================================
// React Hook
// ============================================================================

import { useState, useCallback, useMemo } from 'react';

export function useStateMachine<T extends string>(
  config: StateMachineConfig<T>
): StateMachine<T> {
  const [state, setState] = useState<T>(config.initial);

  const transition = useCallback(
    (event: string) => {
      setState((currentState) => {
        const stateConfig = config.states[currentState];
        const nextState = stateConfig?.on?.[event];
        return nextState ?? currentState;
      });
    },
    [config.states]
  );

  const is = useCallback((checkState: T) => state === checkState, [state]);

  const matches = useCallback(
    (...checkStates: T[]) => checkStates.includes(state),
    [state]
  );

  return useMemo(
    () => ({ state, transition, is, matches }),
    [state, transition, is, matches]
  );
}

// ============================================================================
// Interaction State Hook
// ============================================================================

export function useInteractionState(initialDisabled = false) {
  const machine = useStateMachine({
    initial: initialDisabled ? 'disabled' : 'idle',
    states: interactionStates as StateMachineConfig<InteractionState>['states'],
  });

  const handlers = useMemo(
    () => ({
      onFocus: () => machine.transition('FOCUS'),
      onBlur: () => machine.transition('BLUR'),
      onActivate: () => machine.transition('ACTIVATE'),
      onComplete: () => machine.transition('COMPLETE'),
      onCancel: () => machine.transition('CANCEL'),
      disable: () => machine.transition('DISABLE'),
      enable: () => machine.transition('ENABLE'),
    }),
    [machine]
  );

  return { ...machine, handlers };
}

// ============================================================================
// Async State Hook
// ============================================================================

export function useAsyncState() {
  const machine = useStateMachine({
    initial: 'ready',
    states: asyncStates as StateMachineConfig<AsyncState>['states'],
  });

  const handlers = useMemo(
    () => ({
      start: () => machine.transition('START'),
      success: () => machine.transition('SUCCESS'),
      error: () => machine.transition('ERROR'),
      retry: () => machine.transition('RETRY'),
      reset: () => machine.transition('RESET'),
    }),
    [machine]
  );

  return { ...machine, handlers };
}
