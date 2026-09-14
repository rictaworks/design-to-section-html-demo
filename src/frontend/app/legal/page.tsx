import type { Metadata } from "next";
import Link from "next/link";
import { messages } from "@/lib/messages";

export const metadata: Metadata = {
  title: `${messages.legal.title} | ${messages.site.title}`,
};

export default function LegalPage() {
  const { legal } = messages;
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-col gap-8 px-6 py-12">
      <Link href="/" className="text-sm text-zinc-500 hover:text-zinc-700">
        {legal.backToApp}
      </Link>

      <h1 className="text-xl font-semibold">{legal.title}</h1>

      <section className="flex flex-col gap-3">
        <h2 className="border-b border-zinc-200 pb-2 text-base font-semibold">
          {legal.termsHeading}
        </h2>
        <ul className="flex list-disc flex-col gap-2 pl-5 text-sm text-zinc-600">
          {legal.terms.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="border-b border-zinc-200 pb-2 text-base font-semibold">
          {legal.disclaimerHeading}
        </h2>
        <ul className="flex list-disc flex-col gap-2 pl-5 text-sm text-zinc-600">
          {legal.disclaimer.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="border-b border-zinc-200 pb-2 text-base font-semibold">
          {legal.contactHeading}
        </h2>
        <dl className="flex flex-col gap-2 text-sm">
          <div className="flex gap-4">
            <dt className="w-20 shrink-0 text-zinc-500">{legal.contact.brand}</dt>
            <dd className="text-zinc-700">{legal.contact.brandValue}</dd>
          </div>
          <div className="flex gap-4">
            <dt className="w-20 shrink-0 text-zinc-500">{legal.contact.address}</dt>
            <dd className="text-zinc-700">{legal.contact.addressValue}</dd>
          </div>
          <div className="flex gap-4">
            <dt className="w-20 shrink-0 text-zinc-500">{legal.contact.phone}</dt>
            <dd className="text-zinc-700">{legal.contact.phoneValue}</dd>
          </div>
          <div className="flex gap-4">
            <dt className="w-20 shrink-0 text-zinc-500">{legal.contact.email}</dt>
            <dd className="text-zinc-700">
              <a href={`mailto:${legal.contact.emailValue}`} className="text-zinc-900 underline">
                {legal.contact.emailValue}
              </a>
            </dd>
          </div>
          <div className="flex gap-4">
            <dt className="w-20 shrink-0 text-zinc-500">{legal.contact.web}</dt>
            <dd className="text-zinc-700">
              <a
                href={legal.contact.webValue}
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-900 underline"
              >
                {legal.contact.webValue}
              </a>
            </dd>
          </div>
          <div className="flex gap-4">
            <dt className="w-20 shrink-0 text-zinc-500">{legal.contact.x}</dt>
            <dd className="text-zinc-700">
              <a
                href="https://x.com/rictaworks"
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-900 underline"
              >
                {legal.contact.xValue}
              </a>
            </dd>
          </div>
          <div className="flex gap-4">
            <dt className="w-20 shrink-0 text-zinc-500">{legal.contact.github}</dt>
            <dd className="text-zinc-700">
              <a
                href="https://github.com/rictaworks"
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-900 underline"
              >
                {legal.contact.githubValue}
              </a>
            </dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
