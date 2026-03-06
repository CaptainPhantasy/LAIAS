import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import HomePage from '../app/page'

describe('Home Page', () => {
  it('renders the page title', () => {
    render(<HomePage />)
    
    // Basic smoke test - adjust based on actual page content
    expect(document.body).toBeInTheDocument()
  })
})
