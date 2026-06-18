export default function Footer() {
  return (
    <footer className="bg-cream-deep border-t border-rule pt-16 pb-8">
      <div className="mx-auto max-w-container px-6 lg:px-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10 mb-14">
          <div>
            <div className="h-serif text-[28px] text-ink mb-4">Solvere</div>
            <div className="text-[14px] text-muted leading-[1.6]">
              1WEB FZE
              <br />
              Abu Dhabi, United Arab Emirates
            </div>
          </div>
          <div className="flex md:justify-center">
            <a
              href="mailto:hello@solvere.ai"
              className="text-[15px] text-ink-soft hover:text-teal transition-colors h-serif"
            >
              hello@solvere.ai
            </a>
          </div>
          <div>
            <div className="text-[11px] tracking-[0.22em] uppercase text-muted mb-3">
              Compliance
            </div>
            <p className="text-[13px] text-muted leading-[1.65] max-w-[36ch]">
              DIFC Data Protection Law compliant. No protected health
              information is collected via this website. Sensitive data
              exchange occurs only after a signed NDA via secure encrypted
              channels.
            </p>
          </div>
        </div>

        <div className="pt-6 border-t border-rule text-center text-[12px] tracking-[0.18em] uppercase text-muted">
          © 2026 1WEB FZE. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
