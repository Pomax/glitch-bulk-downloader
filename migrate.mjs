#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import fetch from 'node-fetch';
import dotenv from 'dotenv';

dotenv.config();

const {
  R2_ACCESS_KEY_ID,
  R2_SECRET_ACCESS_KEY,
  R2_ACCOUNT_ID,
  R2_BUCKET_NAME,
  R2_PUBLIC_URL
} = process.env;

if (!R2_ACCESS_KEY_ID || !R2_SECRET_ACCESS_KEY || !R2_ACCOUNT_ID || !R2_BUCKET_NAME) {
  console.error('R2 credentials are missing in environment variables');
  process.exit(1);
}

const endpoint = `https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com`;

const s3 = new S3Client({
  region: 'auto',
  endpoint,
  credentials: {
    accessKeyId: R2_ACCESS_KEY_ID,
    secretAccessKey: R2_SECRET_ACCESS_KEY,
  },
});

async function upload(filename, data, contentType) {
  const command = new PutObjectCommand({
    Bucket: R2_BUCKET_NAME,
    Key: filename,
    Body: data,
    ContentType: contentType,
  });
  await s3.send(command);
}

async function download(url) {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to download ${url}: ${res.statusText}`);
  }
  const buffer = await res.buffer();
  const contentType = res.headers.get('content-type') || undefined;
  return { buffer, contentType };
}

async function processAsset(asset) {
  const parsed = new URL(asset.url);
  const filename = decodeURIComponent(path.basename(parsed.pathname));
  const { buffer, contentType } = await download(asset.url);
  await upload(filename, buffer, contentType);
  return { oldUrl: asset.url, newUrl: `${R2_PUBLIC_URL}/${filename}` };
}

async function migrate() {
  const lines = fs.existsSync('.glitch-assets')
    ? fs.readFileSync('.glitch-assets', 'utf8').split('\n').filter(Boolean)
    : [];
  const assets = lines
    .map((l) => JSON.parse(l))
    .filter((a) => a.url && a.url.includes('cdn.glitch.global'));

  const map = {};
  for (const asset of assets) {
    if (map[asset.url]) continue;
    try {
      const { newUrl } = await processAsset(asset);
      map[asset.url] = newUrl;
      console.log(`${asset.url} -> ${newUrl}`);
    } catch (err) {
      console.error(err.message);
    }
  }

  const files = [];
  function walk(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (entry.name === 'node_modules' || entry.name === '.git') continue;
      const p = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(p);
      else files.push(p);
    }
  }
  walk('.');

  for (const f of files) {
    let data = fs.readFileSync(f, 'utf8');
    let changed = false;
    for (const [oldUrl, newUrl] of Object.entries(map)) {
      if (data.includes(oldUrl)) {
        data = data.split(oldUrl).join(newUrl);
        changed = true;
      }
    }
    if (changed) fs.writeFileSync(f, data, 'utf8');
  }
}

migrate().catch((err) => {
  console.error(err);
  process.exit(1);
});

