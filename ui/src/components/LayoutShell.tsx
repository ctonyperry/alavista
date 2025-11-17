import { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import clsx from "clsx";

type NavItem = {
  label: string;
  path: string;
};

type LayoutShellProps = {
  navItems: NavItem[];
  children: ReactNode;
  title?: string;
  rightSlot?: ReactNode;
};

export function LayoutShell({ navItems, children, rightSlot, title }: LayoutShellProps) {
  const location = useLocation();
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="flex h-screen">
        <aside className="w-60 shrink-0 border-r border-border bg-card">
          <div className="px-4 py-5 text-lg font-semibold">Alavista UI</div>
          <nav className="flex flex-col gap-1 px-2">
            {navItems.map((item) => {
              const active = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={clsx(
                    "rounded-md px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground",
                    active && "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground"
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>
        <main className="flex flex-1 flex-col">
          <header className="flex items-center justify-between border-b border-border px-6 py-4">
            <div>
              <h1 className="text-xl font-semibold">{title ?? "Dashboard"}</h1>
            </div>
            <div className="flex items-center gap-3 text-sm text-muted-foreground">{rightSlot}</div>
          </header>
          <section className="flex-1 overflow-auto bg-background px-6 py-6">{children}</section>
        </main>
      </div>
    </div>
  );
}

export default LayoutShell;
