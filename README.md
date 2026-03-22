# Bomber Command Memorial Register

A community heritage project cataloguing WW2 Bomber Command crash sites and memorials across the UK and internationally.

**Live site:** [bombermemorial.co.uk](https://bombermemorial.co.uk)

## About

The Bomber Command Memorial Register documents over 200 crash sites and memorials from World War II. Each entry captures the human stories behind the memorials — the crews who flew, the communities that remember them, and the local organisations that maintain these sites.

This is a living heritage project, not just a database. We want every memorial to tell a story.

## Data

Memorial records are stored as individual JSON files in `public/data/memorials/`. Each file follows our [memorial schema](https://bombermemorial.co.uk/schema/memorial.json) (v2.1) which includes:

- **Location** — coordinates, What3Words addresses, OS grid references, directions
- **Crash event** — date, aircraft, crew, narrative account
- **Memorial details** — type, condition, inscription, photographs
- **Local contacts** — British Legion branches, parish councils, history societies
- **External narratives** — aggregated stories from other heritage sites
- **Sources** — CWGC, IWM, Aircrew Remembered, local archives

## Contributing

We welcome contributions from anyone with knowledge of bomber crash sites and memorials. You can help by:

1. **Adding new memorials** — Create a JSON file in `public/data/memorials/` following the schema
2. **Enriching existing records** — Add crew details, narratives, photographs, or sources
3. **Adding What3Words locations** — Visit a memorial and record its W3W address
4. **Connecting local contacts** — Know a British Legion branch or history society that maintains a memorial? Add their details
5. **Reporting issues** — Spot an error? Open an issue

### How to contribute

1. Fork this repository
2. Create a branch for your changes
3. Add or edit memorial JSON files
4. Submit a pull request with a description of what you've added

Or email [admin@bombermemorial.co.uk](mailto:admin@bombermemorial.co.uk) if you'd prefer not to use GitHub.

## Tech Stack

- **Next.js 14** — Static site generation
- **TypeScript** — Type-safe memorial data
- **Leaflet** — Interactive maps
- **Tailwind CSS** — Styling

## Development

```bash
npm install
npm run dev     # Development server on localhost:3000
npm run build   # Static export to out/
```

## Key Sources

- [Commonwealth War Graves Commission](https://www.cwgc.org)
- [Aircrew Remembered](https://aircrewremembered.com)
- [Imperial War Museum](https://www.iwm.org.uk)
- Local British Legion branches, parish councils, and history societies

## Data Repository

Memorial data is also available in the companion data repo: [kbgit-coder/bomber-memorial-data](https://github.com/kbgit-coder/bomber-memorial-data)

## License

Memorial data is shared for heritage and educational purposes. Please credit the Bomber Command Memorial Register when reusing.
