import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ControlRoomPage from '../app/page'

describe('Control Room Page', () => {
  it('renders the page', () => {
    render(<ControlRoomPage />)
    
    // Basic smoke test
    expect(document.body).toBeInTheDocument()
  })
})
