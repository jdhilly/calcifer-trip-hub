<script lang="ts">
	import '../app.css';
	import { page } from '$app/state';
	import { NavShell, type NavItem } from '@calcifer/ui';
	import { Compass, Library } from '@lucide/svelte/icons';

	let { children } = $props();

	const items: NavItem[] = [
		{ id: 'dashboard', label: 'Voyages', href: '/', icon: Compass },
		{ id: 'catalog', label: 'Catalogue', href: '/catalog', icon: Library },
	];

	let title = $derived('Trip Hub');
</script>

<NavShell {items} pathname={page.url.pathname} {title} tagline="préparer les valises">
	{@render children()}
</NavShell>
