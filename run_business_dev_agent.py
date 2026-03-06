#!/usr/bin/env python3
"""
Script to run the Indiana SMB Business Development Agent
"""

import asyncio
import sys
import os

# Add the agents directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.indiana_smb_business_development import main

if __name__ == "__main__":
    print("Starting Indiana SMB Business Development Agent...")
    print("This agent will help you find and acquire clients for custom software,")
    print("websites, and AI integration services in the Indiana SMB market.")
    print("")
    print("The agent will:")
    print("1. Research the Indiana SMB market for prospects")
    print("2. Create personalized outreach content")
    print("3. Execute multi-channel outreach campaigns")
    print("4. Qualify leads using the BANT framework")
    print("5. Develop proposals and close deals")
    print("6. Analyze metrics and optimize strategies")
    print("")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)