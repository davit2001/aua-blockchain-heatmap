This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.




##  Bitcoin Node Crawler (Initial Setup)

This is an **initial version** of the Bitcoin network crawler.

It connects to peers using the Bitcoin P2P protocol, discovers new nodes,  
and stores them in a local SQLite database (`nodes.db`).

###  Requirements
- Python 3.8+
- Dependencies: `aiosqlite`
```bash
pip install aiosqlite
```

###  How to Run

1. Go to the script folder:
```bash
cd src/scripts
```
2. Run the crawler:
```bash
python crawler.py
```

You can optionally specify seeds, concurrency, and iterations:
```bash
python crawler.py --seeds seed.bitcoin.sipa.be --iterations 3 --concurrency 200
```

### Output
A SQLite database nodes.db is created in the same folder.  
The database contains a table nodes with discovered IPs.


### Check the results
To see the first 10 nodes:
```bash
sqlite3 nodes.db "SELECT * FROM nodes LIMIT 10;"
```
To count all nodes:
```bash
sqlite3 nodes.db "SELECT COUNT(*) FROM nodes;"
```