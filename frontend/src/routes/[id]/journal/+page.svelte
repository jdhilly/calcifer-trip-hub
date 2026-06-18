<script lang="ts">
	import { PageHeader, Button } from '@calcifer/ui';
	import { Plus, X, BookOpen } from '@lucide/svelte/icons';

	let { data } = $props();
	let trip = $derived(data.trip);
	let entries = $state(data.entries);
	let showForm = $state(false);
	let newContent = $state('');
	let newDate = $state(new Date().toISOString().slice(0, 10));
	let newAuthor = $state('');

	async function addEntry() {
		if (!newContent.trim()) return;
		const r = await fetch('/' + trip.id + '/journal?/add', { method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({content:newContent.trim(),date:newDate,author:newAuthor.trim()}) });
		if ((await r.json()).ok) window.location.reload();
	}
	async function delEntry(id: number) {
		if (!confirm('Supprimer ?')) return;
		const r = await fetch('/' + trip.id + '/journal?/delete', { method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({entryId:String(id)}) });
		if ((await r.json()).ok) entries = entries.filter((e:any) => e.id !== id);
	}
	function fmtDate(d: string) { return new Date(d+'T12:00:00').toLocaleDateString('fr-FR', { weekday:'long', day:'numeric', month:'long', year:'numeric' }); }
</script>

<div class="mx-auto max-w-4xl px-4 py-6">
	<PageHeader title="Journal de bord" backHref={`/${trip.id}`} description={trip.destination} />

	<button onclick={() => (showForm = !showForm)}
		class="mb-6 inline-flex items-center gap-1.5 rounded-lg border border-coal-700 bg-coal-900 px-3 py-1.5 text-xs text-coal-300 transition-colors hover:border-ember-500 hover:text-ember-400">
		<Plus size={14} /> {showForm ? 'Annuler' : 'Nouvelle entrée'}
	</button>

	{#if showForm}
		<div class="mb-6 rounded-2xl border border-coal-800 bg-coal-900/55 p-4">
			<div class="mb-3 flex flex-wrap gap-2">
				<input type="date" bind:value={newDate} class="rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none focus:border-ember-500" />
				<input bind:value={newAuthor} placeholder="Auteur" class="min-w-[150px] flex-1 rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none placeholder:text-coal-400 focus:border-ember-500" />
			</div>
			<textarea bind:value={newContent} placeholder="Que s'est-il passé aujourd'hui ?" rows="4"
				class="mb-3 w-full rounded-lg border border-coal-700 bg-coal-900 p-3 text-sm text-coal-50 outline-none placeholder:text-coal-400 focus:border-ember-500"></textarea>
			<Button onclick={addEntry} disabled={!newContent.trim()}>Publier</Button>
		</div>
	{/if}

	{#if entries.length > 0}
		<div class="mt-6 space-y-4">
			{#each entries as entry (entry.id)}
				<div class="rounded-2xl border border-coal-800 bg-coal-900/55 p-4">
					<div class="mb-2 flex items-center justify-between">
						<div class="flex items-center gap-2">
							<BookOpen size={16} class="shrink-0 text-coal-500" />
							<span class="font-display text-base text-coal-50">{fmtDate(entry.date)}</span>
							{#if entry.author}<span class="rounded bg-coal-800 px-2 py-0.5 text-xs text-coal-400">{entry.author}</span>{/if}
						</div>
						<button onclick={() => delEntry(entry.id)} class="text-coal-600 hover:text-red-400"><X size={14} /></button>
					</div>
					<p class="whitespace-pre-wrap text-sm leading-relaxed text-coal-200">{entry.content}</p>
				</div>
			{/each}
		</div>
	{:else}
		<div class="rounded-2xl border border-coal-800 bg-coal-900/55 p-8 text-center"><p class="text-coal-500">Aucune entrée.</p></div>
	{/if}
</div>
