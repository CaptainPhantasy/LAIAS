import Link from 'next/link';
import Image from 'next/image';
import { Sparkles, ArrowRight, Bot, Code, Rocket, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 h-14 border-b border-border bg-surface/50">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-accent-cyan/20 flex items-center justify-center">
              <span className="text-accent-cyan font-bold text-sm">L</span>
            </div>
            <span className="text-lg font-semibold">LAIAS Studio</span>
          </Link>
        </div>
        <nav className="flex items-center gap-4">
          <Link href="/templates" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
            Templates
          </Link>
          <Link href="/agents" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
            Agents
          </Link>
          <Link href="/create">
            <Button variant="primary" size="sm">
              Create Agent
            </Button>
          </Link>
        </nav>
      </header>

      {/* Hero Section with Godzilla */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-12 relative overflow-hidden">
        {/* Godzilla Hero Image Background */}
        <div className="absolute inset-0 z-0">
          <Image
            src="/godzilla-hero.jpg"
            alt="Godzilla - The Supreme Operator"
            fill
            className="object-cover opacity-20"
            priority
          />
          <div className="absolute inset-0 bg-gradient-to-b from-bg-primary/80 via-bg-primary/60 to-bg-primary" />
        </div>

        <div className="text-center max-w-3xl mx-auto relative z-10">
          {/* Badge */}
          <Badge variant="cyan" size="md" className="mb-6">
            <Sparkles className="w-3.5 h-3.5 mr-1.5" />
            LAIAS Studio
          </Badge>

          {/* Headline */}
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 leading-tight">
            Build AI Agents with{' '}
            <span className="text-gradient-brand">Natural Language</span>
          </h1>

          {/* Subheadline */}
          <p className="text-lg md:text-xl text-text-secondary mb-10 max-w-2xl mx-auto leading-relaxed">
            Describe what you want, and let LAIAS generate production-ready
            CrewAI agents following the Godzilla pattern. No boilerplate, just results.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/create">
              <Button variant="primary" size="lg" iconLeft={<Sparkles className="w-5 h-5" />}>
                Create Agent
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
            <Link href="/templates">
              <Button variant="secondary" size="lg">
                Browse Templates
              </Button>
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6 mt-16 max-w-4xl mx-auto w-full relative z-10">
          <FeatureCard
            icon={<Bot className="w-6 h-6" />}
            title="Describe Your Agent"
            description="Write a natural language description of what your agent should do. Be as specific or creative as you like."
          />
          <FeatureCard
            icon={<Code className="w-6 h-6" />}
            title="Review & Edit Code"
            description="Inspect the generated Python code with syntax highlighting. Make adjustments in the Monaco editor."
          />
          <FeatureCard
            icon={<Rocket className="w-6 h-6" />}
            title="Deploy Instantly"
            description="One-click deployment to a containerized environment. Monitor your agents in the Control Room."
          />
        </div>

        {/* Stats or Trust */}
        <div className="flex items-center gap-8 mt-16 text-text-muted relative z-10">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-accent-cyan" />
            <span className="text-sm">Godzilla pattern</span>
          </div>
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-accent-cyan" />
            <span className="text-sm">Multi-agent support</span>
          </div>
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-accent-cyan" />
            <span className="text-sm">Auto-validation</span>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 px-6 border-t border-border">
        <div className="max-w-7xl mx-auto flex justify-between items-center text-sm text-text-muted">
          <span>LAIAS Studio</span>
          <div className="flex gap-6">
            <Link href="/templates" className="hover:text-text-secondary transition-colors">
              Templates
            </Link>
            <Link href="/agents" className="hover:text-text-secondary transition-colors">
              Agents
            </Link>
            <Link
              href="http://localhost:3001"
              className="hover:text-text-secondary transition-colors"
            >
              Control Room
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="p-6 bg-surface rounded-lg border border-border hover:border-border-strong transition-colors group">
      <div className="w-12 h-12 flex items-center justify-center rounded-lg bg-bg-tertiary text-accent-cyan mb-4 group-hover:shadow-glow-cyan transition-shadow">
        {icon}
      </div>
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-sm text-text-secondary leading-relaxed">{description}</p>
    </div>
  );
}
