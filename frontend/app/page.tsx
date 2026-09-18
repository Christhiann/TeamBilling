"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

type User = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
};
type Organization = {
  id: number;
  name: string;
  slug: string;
  members_count: number;
};
type Plan = {
  id: number;
  name: string;
  amount: string;
  currency: string;
  interval: string;
  active: boolean;
};
type Membership = { id: number; user_email: string; role: string };
type Subscription = {
  plan_name: string;
  status: string;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new Error(
      body.detail ||
        Object.values(body).flat().join(" ") ||
        "Não foi possível concluir a operação.",
    );
  return body;
}

export default function HomePage() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [members, setMembers] = useState<Membership[]>([]);
  const [activeView, setActiveView] = useState("overview");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const signOut = useCallback(() => {
    window.localStorage.removeItem("teambilling_access");
    setToken(null);
    setUser(null);
    setOrganization(null);
  }, []);

  const selectOrganization = useCallback(
    async (selected: Organization, accessToken = token) => {
      if (!accessToken) return;
      setOrganization(selected);
      setError("");
      const [team, billing] = await Promise.all([
        request<Membership[]>(
          `/api/organizations/${selected.id}/members/`,
          {},
          accessToken,
        ),
        request<Subscription>(
          `/api/billing/subscription/?organization_id=${selected.id}`,
          {},
          accessToken,
        ).catch(() => null),
      ]);
      setMembers(team);
      setSubscription(billing);
    },
    [token],
  );

  const loadWorkspace = useCallback(
    async (accessToken: string) => {
      try {
        const [me, orgs, availablePlans] = await Promise.all([
          request<User>("/api/auth/me/", {}, accessToken),
          request<Organization[]>("/api/organizations/", {}, accessToken),
          request<Plan[]>("/api/billing/plans/", {}, accessToken),
        ]);
        setUser(me);
        setOrganizations(orgs);
        setPlans(availablePlans);
        if (orgs.length) await selectOrganization(orgs[0], accessToken);
      } catch (caught) {
        signOut();
        setError(caught instanceof Error ? caught.message : "Sessão expirada.");
      } finally {
        setLoading(false);
      }
    },
    [selectOrganization, signOut],
  );

  useEffect(() => {
    const savedToken = window.localStorage.getItem("teambilling_access");
    if (!savedToken) {
      setLoading(false);
      return;
    }
    setToken(savedToken);
    loadWorkspace(savedToken);
  }, [loadWorkspace]);
  async function submitAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const data = Object.fromEntries(new FormData(event.currentTarget));
    try {
      const result = await request<{ token: { access: string }; user: User }>(
        `/api/auth/${authMode === "login" ? "token" : "register"}/`,
        { method: "POST", body: JSON.stringify(data) },
      );
      const accessToken = result.token.access;
      window.localStorage.setItem("teambilling_access", accessToken);
      setToken(accessToken);
      setUser(result.user);
      await loadWorkspace(accessToken);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Não foi possível entrar.",
      );
      setLoading(false);
    }
  }
  async function createOrganization(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    try {
      const created = await request<Organization>(
        "/api/organizations/",
        {
          method: "POST",
          body: JSON.stringify(
            Object.fromEntries(new FormData(event.currentTarget)),
          ),
        },
        token,
      );
      setOrganizations([...organizations, created]);
      await selectOrganization(created);
      setNotice("Organização criada com sucesso.");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Não foi possível criar a organização.",
      );
    }
  }
  async function addMember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !organization) return;
    try {
      await request(
        `/api/organizations/${organization.id}/members/add/`,
        {
          method: "POST",
          body: JSON.stringify(
            Object.fromEntries(new FormData(event.currentTarget)),
          ),
        },
        token,
      );
      await selectOrganization(organization);
      setNotice("Membro adicionado.");
      event.currentTarget.reset();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Não foi possível adicionar o membro.",
      );
    }
  }
  async function startCheckout(plan: Plan) {
    if (!token || !organization) return;
    try {
      const result = await request<{ checkout_url: string }>(
        "/api/billing/checkout/",
        {
          method: "POST",
          body: JSON.stringify({
            organization_id: organization.id,
            plan: plan.name,
          }),
        },
        token,
      );
      window.open(result.checkout_url, "_blank", "noopener,noreferrer");
      setNotice(`Checkout do plano ${plan.name} aberto.`);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Não foi possível iniciar o checkout.",
      );
    }
  }
  const initials = (name: string) =>
    name
      .split(" ")
      .map((part) => part[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  const money = (amount: string, currency: string) =>
    new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: currency.toUpperCase(),
    }).format(Number(amount));
  if (loading)
    return (
      <div className="loading-screen">
        <div className="brand-mark">TB</div>
        <p>Preparando seu workspace...</p>
      </div>
    );
  if (!token || !user)
    return (
      <AuthScreen
        mode={authMode}
        setMode={setAuthMode}
        onSubmit={submitAuth}
        error={error}
      />
    );
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">TB</span>
          <span>teambilling</span>
        </div>
        <div className="workspace-label">Workspace</div>
        <select
          className="org-select"
          value={organization?.id || ""}
          onChange={(event) => {
            const selected = organizations.find(
              (item) => item.id === Number(event.target.value),
            );
            if (selected) selectOrganization(selected);
          }}
        >
          {organizations.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <nav className="nav-list">
          {[
            ["overview", "Visão geral", "⌂"],
            ["billing", "Faturamento", "◈"],
            ["team", "Equipe", "♧"],
          ].map(([id, label, icon]) => (
            <button
              className={activeView === id ? "nav-item active" : "nav-item"}
              key={id}
              onClick={() => setActiveView(id)}
            >
              <span>{icon}</span>
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <button
            className="nav-item"
            onClick={() => setActiveView("settings")}
          >
            <span>⚙</span>Configurações
          </button>
          <div className="profile-mini">
            <div className="avatar">
              {initials(`${user.first_name} ${user.last_name}`)}
            </div>
            <div>
              <strong>{user.first_name || user.email.split("@")[0]}</strong>
              <small>{user.email}</small>
            </div>
            <button className="icon-button" title="Sair" onClick={signOut}>
              ↪
            </button>
          </div>
        </div>
      </aside>
      <main className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">{organization?.name || "Seu workspace"}</p>
            <h1>
              {activeView === "overview"
                ? "Visão geral"
                : activeView === "billing"
                  ? "Faturamento"
                  : activeView === "team"
                    ? "Equipe"
                    : "Configurações"}
            </h1>
          </div>
          <div className="topbar-actions">
            <span className="status-dot">Tudo operando</span>
            <button className="avatar avatar-large">
              {initials(`${user.first_name} ${user.last_name}`)}
            </button>
          </div>
        </header>
        {notice && (
          <div className="notice success">
            {notice}
            <button onClick={() => setNotice("")}>×</button>
          </div>
        )}
        {error && (
          <div className="notice error">
            {error}
            <button onClick={() => setError("")}>×</button>
          </div>
        )}
        {!organizations.length ? (
          <EmptyWorkspace onSubmit={createOrganization} />
        ) : activeView === "team" ? (
          <TeamView members={members} onSubmit={addMember} />
        ) : activeView === "billing" ? (
          <BillingView
            plans={plans}
            subscription={subscription}
            onCheckout={startCheckout}
            money={money}
          />
        ) : activeView === "settings" ? (
          <SettingsView user={user} initials={initials} />
        ) : (
          <Overview
            organization={organization}
            subscription={subscription}
            members={members}
            plans={plans}
            onBilling={() => setActiveView("billing")}
            onTeam={() => setActiveView("team")}
          />
        )}
      </main>
    </div>
  );
}

function AuthScreen({
  mode,
  setMode,
  onSubmit,
  error,
}: {
  mode: "login" | "register";
  setMode: (mode: "login" | "register") => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  error: string;
}) {
  return (
    <main className="auth-page">
      <section className="auth-visual">
        <div className="brand brand-light">
          <span className="brand-mark">TB</span>
          <span>teambilling</span>
        </div>
        <div className="visual-copy">
          <p className="eyebrow">Billing sem atrito</p>
          <h1>Mais clareza para cada decisão do seu time.</h1>
          <p>Controle organizações, planos e assinaturas em um único lugar.</p>
        </div>
        <div className="visual-stat">
          <strong>+24%</strong>
          <span>visibilidade financeira</span>
        </div>
      </section>
      <section className="auth-panel">
        <div className="auth-box">
          <p className="eyebrow">
            {mode === "login" ? "Bem-vindo de volta" : "Comece agora"}
          </p>
          <h2>
            {mode === "login" ? "Entre no seu workspace" : "Crie sua conta"}
          </h2>
          <p className="muted">
            {mode === "login"
              ? "Acompanhe seu billing em tempo real."
              : "Configure seu primeiro workspace em minutos."}
          </p>
          <div className="auth-tabs">
            <button
              className={mode === "login" ? "selected" : ""}
              onClick={() => setMode("login")}
            >
              Entrar
            </button>
            <button
              className={mode === "register" ? "selected" : ""}
              onClick={() => setMode("register")}
            >
              Criar conta
            </button>
          </div>
          <form onSubmit={onSubmit} className="form-stack">
            {mode === "register" && (
              <div className="field-row">
                <label>
                  Nome
                  <input name="first_name" required placeholder="Ana" />
                </label>
                <label>
                  Sobrenome
                  <input name="last_name" required placeholder="Silva" />
                </label>
              </div>
            )}
            <label>
              E-mail
              <input
                type="email"
                name="email"
                required
                placeholder="voce@empresa.com"
              />
            </label>
            <label>
              Senha
              <input
                type="password"
                name="password"
                required
                minLength={8}
                placeholder="Mínimo de 8 caracteres"
              />
            </label>
            <button className="primary-button" type="submit">
              {mode === "login" ? "Acessar workspace" : "Criar minha conta"}
              <span>→</span>
            </button>
          </form>
          {error && <p className="form-error">{error}</p>}
          <p className="fine-print">
            Ao continuar, você concorda com os termos de uso do TeamBilling.
          </p>
        </div>
      </section>
    </main>
  );
}

function Overview({
  organization,
  subscription,
  members,
  plans,
  onBilling,
  onTeam,
}: {
  organization: Organization | null;
  subscription: Subscription | null;
  members: Membership[];
  plans: Plan[];
  onBilling: () => void;
  onTeam: () => void;
}) {
  const currentPlan = subscription?.plan_name || "FREE";
  return (
    <div className="view-stack">
      <section className="hero-banner">
        <div>
          <p className="eyebrow">Resumo do mês</p>
          <h2>Olá, vamos manter as contas em ordem.</h2>
          <p>
            Seu workspace está pronto para acompanhar crescimento e recorrência.
          </p>
        </div>
        <div className="hero-orbit">
          <span>✦</span>
          <strong>{organization?.members_count || members.length}</strong>
          <small>pessoas no time</small>
        </div>
      </section>
      <div className="metric-grid">
        <Metric
          label="Plano atual"
          value={currentPlan}
          note={
            subscription
              ? `Status: ${subscription.status.toLowerCase()}`
              : "Comece pelo plano ideal"
          }
          accent="mint"
        />
        <Metric
          label="Membros ativos"
          value={String(organization?.members_count || members.length)}
          note="Acesso ao workspace"
          accent="yellow"
        />
        <Metric
          label="Planos disponíveis"
          value={String(plans.length)}
          note="Opções para escalar"
          accent="coral"
        />
      </div>
      <section className="section-heading">
        <div>
          <p className="eyebrow">Próximos passos</p>
          <h2>Central de operações</h2>
        </div>
        <span className="muted">Atualizado agora</span>
      </section>
      <div className="action-grid">
        <button className="action-card" onClick={onBilling}>
          <span className="action-icon mint">◈</span>
          <strong>Escolher um plano</strong>
          <span>Compare opções e ative o billing.</span>
          <b>Ver planos →</b>
        </button>
        <button className="action-card" onClick={onTeam}>
          <span className="action-icon coral">♧</span>
          <strong>Convidar equipe</strong>
          <span>Adicione pessoas ao seu workspace.</span>
          <b>Gerenciar equipe →</b>
        </button>
        <div className="action-card static-card">
          <span className="action-icon yellow">✓</span>
          <strong>Workspace protegido</strong>
          <span>Permissões por organização ativas.</span>
          <b className="secure-label">Seguro e verificado</b>
        </div>
      </div>
    </div>
  );
}
function Metric({
  label,
  value,
  note,
  accent,
}: {
  label: string;
  value: string;
  note: string;
  accent: string;
}) {
  return (
    <div className={`metric-card ${accent}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}
function BillingView({
  plans,
  subscription,
  onCheckout,
  money,
}: {
  plans: Plan[];
  subscription: Subscription | null;
  onCheckout: (plan: Plan) => void;
  money: (amount: string, currency: string) => string;
}) {
  return (
    <div className="view-stack">
      <section className="section-heading">
        <div>
          <p className="eyebrow">Assinatura</p>
          <h2>Escolha o ritmo do seu crescimento.</h2>
          <p className="muted">
            Planos flexíveis para acompanhar cada fase da operação.
          </p>
        </div>
        {subscription && (
          <span className="pill active-pill">● {subscription.status}</span>
        )}
      </section>
      <div className="plans-grid">
        {plans.map((plan, index) => (
          <article
            className={`plan-card ${index === 1 ? "featured" : ""}`}
            key={plan.id}
          >
            {index === 1 && <span className="popular">Mais escolhido</span>}
            <div className="plan-top">
              <span className="plan-symbol">
                {index === 0 ? "○" : index === 1 ? "◆" : "✦"}
              </span>
              <span className="plan-name">{plan.name}</span>
            </div>
            <p className="plan-description">
              {plan.name === "FREE"
                ? "Para começar com o essencial."
                : plan.name === "PRO"
                  ? "Para times que querem acelerar."
                  : "Para operações em escala."}
            </p>
            <div className="plan-price">
              {money(plan.amount, plan.currency)}
              <small>/{plan.interval === "month" ? "mês" : "ano"}</small>
            </div>
            <ul>
              <li>Organizações e membros</li>
              <li>Dashboard financeiro</li>
              <li>Suporte operacional</li>
            </ul>
            <button
              className={index === 1 ? "primary-button" : "secondary-button"}
              onClick={() => onCheckout(plan)}
              disabled={plan.name === "FREE"}
            >
              {plan.name === "FREE" ? "Plano atual" : "Começar agora"}
              <span>→</span>
            </button>
          </article>
        ))}
      </div>
      {!plans.length && (
        <div className="empty-state">
          <strong>Nenhum plano disponível ainda.</strong>
          <span>Execute seed_plans no backend para carregar os planos.</span>
        </div>
      )}
    </div>
  );
}
function TeamView({
  members,
  onSubmit,
}: {
  members: Membership[];
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <div className="view-stack">
      <section className="section-heading">
        <div>
          <p className="eyebrow">Colaboração</p>
          <h2>As pessoas do seu workspace.</h2>
          <p className="muted">
            Mantenha as permissões e acessos sob controle.
          </p>
        </div>
      </section>
      <div className="team-layout">
        <section className="panel">
          <div className="panel-heading">
            <h3>Membros</h3>
            <span className="count-badge">{members.length}</span>
          </div>
          <div className="member-list">
            {members.map((member) => (
              <div className="member-row" key={member.id}>
                <div className="avatar">
                  {member.user_email.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <strong>{member.user_email}</strong>
                  <small>
                    {member.role === "OWNER" ? "Proprietário" : "Membro"}
                  </small>
                </div>
                <span className="role-label">{member.role}</span>
              </div>
            ))}
          </div>
        </section>
        <section className="panel invite-panel">
          <span className="action-icon coral">+</span>
          <h3>Convide alguém</h3>
          <p className="muted">
            A pessoa precisa ter uma conta TeamBilling antes de ser adicionada.
          </p>
          <form onSubmit={onSubmit} className="form-stack">
            <label>
              E-mail do membro
              <input
                type="email"
                name="email"
                required
                placeholder="colega@empresa.com"
              />
            </label>
            <button className="primary-button" type="submit">
              Adicionar membro <span>→</span>
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}
function EmptyWorkspace({
  onSubmit,
}: {
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <div className="empty-workspace">
      <div className="empty-illustration">✦</div>
      <p className="eyebrow">Primeiro passo</p>
      <h2>Crie seu workspace.</h2>
      <p>
        Organize o billing da sua empresa em um espaço simples e compartilhado.
      </p>
      <form onSubmit={onSubmit} className="create-form">
        <input name="name" required placeholder="Nome da organização" />
        <button className="primary-button" type="submit">
          Criar workspace <span>→</span>
        </button>
      </form>
    </div>
  );
}
function SettingsView({
  user,
  initials,
}: {
  user: User;
  initials: (name: string) => string;
}) {
  return (
    <div className="view-stack">
      <section className="section-heading">
        <div>
          <p className="eyebrow">Preferências</p>
          <h2>Configurações da conta.</h2>
        </div>
      </section>
      <section className="panel settings-panel">
        <div className="settings-avatar">
          {initials(`${user.first_name} ${user.last_name}`)}
        </div>
        <div>
          <h3>
            {user.first_name} {user.last_name}
          </h3>
          <p className="muted">{user.email}</p>
        </div>
        <span className="pill">Conta ativa</span>
      </section>
    </div>
  );
}
