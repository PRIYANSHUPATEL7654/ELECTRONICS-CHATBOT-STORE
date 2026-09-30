import React, {useEffect, useState} from 'react'
import {createRoot} from 'react-dom/client'
import './index.css'
import {request} from './api'

const money = value => `₹${Number(value).toLocaleString('en-IN')}`
const dateTime = value => new Intl.DateTimeFormat('en-IN', {dateStyle: 'medium', timeStyle: 'short'}).format(new Date(value))
const monthKey = value => {
  const date = new Date(value)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}
const monthLabel = key => new Intl.DateTimeFormat('en-IN', {month: 'long', year: 'numeric'}).format(new Date(`${key}-01T00:00:00`))
const emptyProduct = {name: '', description: '', price: '', category: 'Phones', stock: '', image_url: 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=900&q=80'}
const initial = {answer: 'Hi! I’m ElectroChat. Ask me about phones, laptops, headphones, prices, stock, or recommendations.', products: [], suggestions: ['Show me phones', 'Find budget laptops', 'Recommend headphones']}

function ProductCard({product, onOrder}) {
  return <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
    <img src={product.image_url} alt={product.name} className="h-36 w-full object-cover"/>
    <div className="p-4">
      <div className="mb-1 flex items-start justify-between gap-2"><h3 className="font-bold leading-tight">{product.name}</h3><span className="rounded-full bg-indigo-50 px-2 py-1 text-xs font-semibold text-indigo-700">{product.category}</span></div>
      <p className="mt-2 line-clamp-2 text-sm text-slate-500">{product.description}</p>
      <div className="mt-4 flex items-center justify-between"><div><p className="text-lg font-bold text-slate-900">{money(product.price)}</p><p className={product.stock ? 'text-xs text-emerald-600' : 'text-xs text-red-600'}>{product.stock ? `${product.stock} in stock` : 'Out of stock'}</p></div><button disabled={!product.stock} onClick={() => onOrder(product)} className="rounded-xl bg-slate-900 px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40">Order now</button></div>
    </div>
  </div>
}

function OrderModal({product, close}) {
  const [form, setForm] = useState({customer_name: '', customer_email: '', customer_address: '', quantity: 1})
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(null)
  const [error, setError] = useState('')

  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('')
    try {
      const result = await request('/orders', {method: 'POST', body: JSON.stringify({customer_name: form.customer_name, customer_email: form.customer_email, customer_address: form.customer_address, items: [{product_id: product.id, quantity: Number(form.quantity)}]})})
      setDone(result)
    } catch (err) { setError(err.message) } finally { setBusy(false) }
  }

  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4">
    <div className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl">
      {done ? <><div className="text-4xl">🎉</div><h2 className="mt-3 text-2xl font-bold">Order #{done.id} placed!</h2><p className="mt-2 text-slate-600">Your total is {money(done.total_amount)}. We’ll use your contact details for delivery updates.</p><button onClick={close} className="mt-6 w-full rounded-xl bg-indigo-600 py-3 font-bold text-white">Done</button></> : <>
        <div className="flex items-start justify-between"><div><p className="text-sm text-indigo-600">Ordering</p><h2 className="text-2xl font-bold">{product.name}</h2></div><button onClick={close} className="text-2xl text-slate-400">×</button></div>
        <form onSubmit={submit} className="mt-5 space-y-3">
          {[['customer_name', 'Full name'], ['customer_email', 'Email'], ['customer_address', 'Delivery address']].map(([key, label]) => <input key={key} required minLength={key === 'customer_address' ? 5 : undefined} type={key === 'customer_email' ? 'email' : 'text'} placeholder={label} value={form[key]} onChange={event => setForm({...form, [key]: event.target.value})} className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-indigo-500"/>)}
          <input required min="1" max={product.stock} type="number" placeholder="Quantity" value={form.quantity} onChange={event => setForm({...form, quantity: event.target.value})} className="w-full rounded-xl border border-slate-200 px-4 py-3"/>
          {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          <button disabled={busy} className="w-full rounded-xl bg-indigo-600 py-3 font-bold text-white disabled:opacity-50">{busy ? 'Placing order...' : `Place order · ${money(product.price * form.quantity)}`}</button>
        </form>
      </>}
    </div>
  </div>
}

function Storefront() {
  const [messages, setMessages] = useState([{role: 'bot', ...initial}])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [order, setOrder] = useState(null)

  async function send(text = input) {
    if (!text.trim() || busy) return
    setMessages(messages => [...messages, {role: 'user', text}]); setInput(''); setBusy(true)
    try {
      const result = await request('/chat', {method: 'POST', body: JSON.stringify({message: text})})
      setMessages(messages => [...messages, {role: 'bot', ...result}])
    } catch (err) { setMessages(messages => [...messages, {role: 'bot', answer: `I couldn’t reach the store API: ${err.message}`, products: [], suggestions: []}]) } finally { setBusy(false) }
  }

  return <div className="min-h-screen bg-[radial-gradient(circle_at_top_right,#dbeafe,transparent_35%),radial-gradient(circle_at_bottom_left,#ede9fe,transparent_35%)]">
    <header className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5"><div className="flex items-center gap-3"><div className="grid h-11 w-11 place-items-center rounded-2xl bg-slate-950 text-xl text-white">⚡</div><div><p className="font-bold">ElectroChat</p><p className="text-xs text-slate-500">Smart shopping, simple answers</p></div></div><a href="/admin" className="rounded-xl border border-slate-200 bg-white/70 px-4 py-2 text-sm font-semibold">Admin</a></header>
    <main className="mx-auto grid max-w-7xl gap-6 px-5 pb-10 lg:grid-cols-[1fr_1.45fr]"><section className="flex flex-col justify-center py-8 lg:py-20"><p className="mb-4 w-fit rounded-full bg-indigo-100 px-3 py-1 text-sm font-semibold text-indigo-700">LIVE PRODUCT Q&A + ORDERS</p><h1 className="max-w-xl text-5xl font-bold leading-tight tracking-tight md:text-6xl">Find your next <span className="text-indigo-600">favorite gadget.</span></h1><p className="mt-6 max-w-lg text-lg leading-8 text-slate-600">Ask natural questions. Compare products, check real stock, and place an order without leaving the conversation.</p><div className="mt-8 grid grid-cols-3 gap-3 text-center"><div className="rounded-2xl bg-white/70 p-4"><p className="text-2xl font-bold">50</p><p className="text-xs text-slate-500">products</p></div><div className="rounded-2xl bg-white/70 p-4"><p className="text-2xl font-bold">24/7</p><p className="text-xs text-slate-500">assistant</p></div><div className="rounded-2xl bg-white/70 p-4"><p className="text-2xl font-bold">1 tap</p><p className="text-xs text-slate-500">to order</p></div></div></section>
      <section className="glass flex min-h-[650px] flex-col overflow-hidden rounded-[2rem] border border-white/80 shadow-2xl"><div className="flex items-center justify-between border-b border-slate-200/70 px-5 py-4"><div><h2 className="font-bold">ElectroChat assistant</h2><p className="text-xs text-emerald-600">● Online · store database connected</p></div><span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-500">AI shopping desk</span></div><div className="flex-1 space-y-5 overflow-y-auto p-5">{messages.map((message, index) => <div key={index} className={message.role === 'user' ? 'ml-auto max-w-[82%]' : 'max-w-[95%]'}><div className={message.role === 'user' ? 'rounded-2xl rounded-br-sm bg-indigo-600 px-4 py-3 text-white' : 'rounded-2xl rounded-bl-sm bg-white px-4 py-3 shadow-sm'}>{message.role === 'user' ? message.text : message.answer}</div>{message.products?.length > 0 && <div className="mt-3 grid gap-3 sm:grid-cols-2">{message.products.map(product => <ProductCard key={product.id} product={product} onOrder={setOrder}/>)}</div>}{message.suggestions?.length > 0 && <div className="mt-3 flex flex-wrap gap-2">{message.suggestions.map(suggestion => <button key={suggestion} onClick={() => send(suggestion)} className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-2 text-xs font-semibold text-indigo-700">{suggestion}</button>)}</div>}</div>)}{busy && <div className="text-sm text-slate-400">ElectroChat is checking the catalog…</div>}</div><div className="border-t border-slate-200/70 p-4"><div className="flex gap-2 rounded-2xl bg-white p-2 shadow-inner"><input value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => event.key === 'Enter' && send()} placeholder="Try: show budget laptops in stock" className="min-w-0 flex-1 bg-transparent px-3 py-2 outline-none"/><button onClick={() => send()} className="rounded-xl bg-slate-950 px-5 py-2 font-bold text-white">Send</button></div></div></section>
    </main>
    {order && <OrderModal product={order} close={() => setOrder(null)}/>} 
  </div>
}

function StatusBadge({status}) {
  return <span className={status === 'completed' ? 'rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700' : 'rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-700'}>{status === 'completed' ? 'Completed' : 'Pending'}</span>
}

function StatCard({label, value, detail, tone}) {
  return <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className={`mb-5 grid h-10 w-10 place-items-center rounded-2xl ${tone}`}>✦</div><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-1 text-3xl font-bold tracking-tight text-slate-950">{value}</p><p className="mt-2 text-xs text-slate-400">{detail}</p></div>
}

function Admin() {
  const storedKey = localStorage.getItem('adminKey') || ''
  const [key, setKey] = useState(storedKey)
  const [credentials, setCredentials] = useState({username: '', password: ''})
  const [authed, setAuthed] = useState(Boolean(storedKey))
  const [checking, setChecking] = useState(Boolean(storedKey))
  const [products, setProducts] = useState([])
  const [orders, setOrders] = useState([])
  const [tab, setTab] = useState('products')
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(emptyProduct)
  const [orderStatus, setOrderStatus] = useState('all')
  const [orderMonth, setOrderMonth] = useState('all')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(false)
  const headers = {'X-Admin-Key': key}

  async function load() {
    setLoading(true); setChecking(true); setError('')
    try {
      const [productData, orderData] = await Promise.all([request('/products'), request('/orders', {headers})])
      setProducts(productData); setOrders(orderData); setAuthed(true)
    } catch (err) {
      setError(err.message); setAuthed(false); localStorage.removeItem('adminKey')
    } finally { setLoading(false); setChecking(false) }
  }

  useEffect(() => { if (authed) load(); else setChecking(false) }, [authed])

  function login(event) {
    event.preventDefault(); setError(''); setNotice('')
    if (credentials.username !== 'admin' || credentials.password !== 'admin123') { setError('Use username admin and password admin123.'); return }
    if (!key.trim()) { setError('Enter the ADMIN_API_KEY from the backend environment.'); return }
    localStorage.setItem('adminKey', key.trim()); setAuthed(true)
  }

  function logout() { localStorage.removeItem('adminKey'); setAuthed(false); setProducts([]); setOrders([]); setKey(''); setCredentials({username: '', password: ''}) }

  async function saveProduct(event) {
    event.preventDefault(); setError(''); setNotice('')
    try {
      const payload = {...form, price: Number(form.price), stock: Number(form.stock)}
      await request(editing ? `/products/${editing}` : '/products', {method: editing ? 'PUT' : 'POST', headers, body: JSON.stringify(payload)})
      setEditing(null); setForm(emptyProduct); setNotice(editing ? 'Product updated successfully.' : 'Product added successfully.'); await load()
    } catch (err) { setError(err.message) }
  }

  async function removeProduct(id) {
    if (!window.confirm('Delete this product?')) return
    try { await request(`/products/${id}`, {method: 'DELETE', headers}); setNotice('Product deleted.'); await load() } catch (err) { setError(err.message) }
  }

  async function updateOrderStatus(order) {
    const nextStatus = order.status === 'completed' ? 'pending' : 'completed'
    try { await request(`/orders/${order.id}/status`, {method: 'PATCH', headers, body: JSON.stringify({status: nextStatus})}); setNotice(`Order #${order.id} marked ${nextStatus}.`); await load() } catch (err) { setError(err.message) }
  }

  async function removeOrder(order) {
    if (!window.confirm(`Delete order #${order.id}? Pending order stock will be returned to inventory.`)) return
    try { await request(`/orders/${order.id}`, {method: 'DELETE', headers}); setNotice(`Order #${order.id} deleted.`); await load() } catch (err) { setError(err.message) }
  }

  const pendingOrders = orders.filter(order => order.status === 'pending')
  const completedOrders = orders.filter(order => order.status === 'completed')
  const inventoryUnits = products.reduce((sum, product) => sum + Number(product.stock || 0), 0)
  const monthOptions = [...new Set(orders.map(order => monthKey(order.created_at)))].sort().reverse()
  const filteredOrders = orders.filter(order => (orderStatus === 'all' || order.status === orderStatus) && (orderMonth === 'all' || monthKey(order.created_at) === orderMonth))
  const groupedOrders = filteredOrders.reduce((groups, order) => {
    const key = monthKey(order.created_at)
    const existing = groups.find(group => group.key === key)
    if (existing) existing.orders.push(order); else groups.push({key, orders: [order]})
    return groups
  }, [])

  if (!authed) return <div className="grid min-h-screen place-items-center bg-[radial-gradient(circle_at_top,#312e81,#0f172a_55%)] p-5"><form onSubmit={login} className="w-full max-w-md rounded-[2rem] border border-white/20 bg-white p-8 shadow-2xl"><div className="mb-8 flex items-center gap-3"><div className="grid h-12 w-12 place-items-center rounded-2xl bg-indigo-600 text-xl text-white">⚡</div><div><p className="text-sm font-semibold text-indigo-600">ELECTROCHAT</p><h1 className="text-2xl font-bold">Admin workspace</h1></div></div><p className="mb-5 text-sm leading-6 text-slate-500">Manage products, review customer orders, and keep fulfillment moving.</p><input required placeholder="Username" value={credentials.username} onChange={event => setCredentials({...credentials, username: event.target.value})} className="mb-3 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-indigo-500"/><input required type="password" placeholder="Password" value={credentials.password} onChange={event => setCredentials({...credentials, password: event.target.value})} className="mb-3 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-indigo-500"/><input required value={key} onChange={event => setKey(event.target.value)} placeholder="Backend ADMIN_API_KEY" className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-indigo-500"/>{error && <p className="mt-3 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}<button className="mt-5 w-full rounded-xl bg-indigo-600 py-3 font-bold text-white transition hover:bg-indigo-700">Open dashboard</button><a href="/" className="mt-4 block text-center text-sm font-semibold text-indigo-600">Back to store</a></form></div>

  if (checking) return <div className="grid min-h-screen place-items-center bg-slate-50"><div className="rounded-3xl bg-white p-8 text-center shadow-sm"><div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-indigo-100 border-t-indigo-600"/><p className="font-semibold">Verifying admin access…</p></div></div>

  return <div className="min-h-screen bg-[#f5f7fb]">
    <header className="bg-slate-950 text-white"><div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-4"><a href="/" className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-indigo-500 text-lg">⚡</span><span><span className="block font-bold">ElectroChat</span><span className="block text-xs text-slate-400">Admin command center</span></span></a><div className="flex items-center gap-3"><span className="hidden items-center gap-2 rounded-full bg-emerald-400/10 px-3 py-2 text-xs font-semibold text-emerald-300 sm:flex"><span className="h-2 w-2 rounded-full bg-emerald-400"/> API connected</span><button onClick={load} className="rounded-xl border border-slate-700 px-3 py-2 text-sm font-semibold transition hover:bg-slate-800">↻ Refresh</button><button onClick={logout} className="rounded-xl px-3 py-2 text-sm font-semibold text-slate-300 transition hover:bg-slate-800 hover:text-white">Log out</button></div></div></header>
    <main className="mx-auto max-w-7xl px-5 py-8">
      <section className="mb-8 flex flex-wrap items-end justify-between gap-5"><div><p className="mb-2 text-sm font-bold tracking-[0.2em] text-indigo-600">STORE OPERATIONS</p><h1 className="text-4xl font-bold tracking-tight text-slate-950 md:text-5xl">Good morning, admin.</h1><p className="mt-3 max-w-2xl text-slate-500">Monitor inventory, prioritize pending orders, and keep every customer request moving.</p></div><div className="rounded-2xl border border-indigo-100 bg-indigo-50 px-4 py-3 text-sm text-indigo-700"><p className="font-bold">Today’s focus</p><p className="mt-1">{pendingOrders.length ? `${pendingOrders.length} order${pendingOrders.length === 1 ? '' : 's'} waiting for action` : 'All orders are completed'}</p></div></section>
      <section className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><StatCard label="Total products" value={products.length} detail="Catalog items managed" tone="bg-indigo-100 text-indigo-700"/><StatCard label="Pending orders" value={pendingOrders.length} detail="Prioritized for fulfillment" tone="bg-amber-100 text-amber-700"/><StatCard label="Completed orders" value={completedOrders.length} detail="Successfully processed" tone="bg-emerald-100 text-emerald-700"/><StatCard label="Inventory units" value={inventoryUnits.toLocaleString('en-IN')} detail="Available across catalog" tone="bg-sky-100 text-sky-700"/></section>
      <div className="mb-6 flex flex-wrap gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm"><button onClick={() => setTab('products')} className={tab === 'products' ? 'rounded-xl bg-slate-950 px-5 py-3 text-sm font-bold text-white' : 'rounded-xl px-5 py-3 text-sm font-bold text-slate-500 hover:bg-slate-100'}>Products <span className="ml-1 opacity-70">{products.length}</span></button><button onClick={() => setTab('orders')} className={tab === 'orders' ? 'rounded-xl bg-indigo-600 px-5 py-3 text-sm font-bold text-white' : 'rounded-xl px-5 py-3 text-sm font-bold text-slate-500 hover:bg-slate-100'}>Orders <span className="ml-1 opacity-70">{orders.length}</span></button></div>
      {error && <div className="mb-5 flex items-center justify-between rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700"><span>{error}</span><button onClick={() => setError('')} className="text-lg">×</button></div>}
      {notice && <div className="mb-5 flex items-center justify-between rounded-2xl border border-emerald-100 bg-emerald-50 p-4 text-sm text-emerald-700"><span>{notice}</span><button onClick={() => setNotice('')} className="text-lg">×</button></div>}
      {loading && <div className="mb-5 rounded-2xl bg-indigo-50 p-3 text-center text-sm font-semibold text-indigo-700">Updating dashboard…</div>}

      {tab === 'products' ? <section className="grid gap-6 xl:grid-cols-[360px_1fr]"><form onSubmit={saveProduct} className="h-fit rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="mb-5 flex items-start justify-between"><div><p className="text-xs font-bold tracking-widest text-indigo-600">CATALOG</p><h2 className="mt-1 text-2xl font-bold">{editing ? 'Edit product' : 'Add product'}</h2></div><span className="rounded-xl bg-slate-100 px-3 py-2 text-xs font-bold text-slate-500">{editing ? `#${editing}` : 'NEW'}</span></div>{[['name', 'Product name'], ['description', 'Description'], ['price', 'Price'], ['stock', 'Stock quantity'], ['image_url', 'Image URL']].map(([field, label]) => <input key={field} required={field !== 'image_url'} type={field === 'price' || field === 'stock' ? 'number' : 'text'} placeholder={label} value={form[field]} onChange={event => setForm({...form, [field]: event.target.value})} className="mb-3 w-full rounded-xl border border-slate-200 px-3 py-3 text-sm outline-none transition focus:border-indigo-500"/>)}<select value={form.category} onChange={event => setForm({...form, category: event.target.value})} className="w-full rounded-xl border border-slate-200 px-3 py-3 text-sm outline-none focus:border-indigo-500"><option>Phones</option><option>Laptops</option><option>Headphones</option><option>Earbuds</option><option>Smartwatches</option><option>Cameras</option><option>Accessories</option></select><button className="mt-4 w-full rounded-xl bg-slate-950 py-3 font-bold text-white transition hover:bg-indigo-600">{editing ? 'Save changes' : 'Add product'}</button>{editing && <button type="button" onClick={() => {setEditing(null); setForm(emptyProduct)}} className="mt-2 w-full rounded-xl py-2 text-sm font-semibold text-slate-500 hover:bg-slate-50">Cancel editing</button>}</form>
        <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm"><div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 p-5"><div><h2 className="text-xl font-bold">Product inventory</h2><p className="mt-1 text-sm text-slate-500">Current catalog stock and pricing.</p></div><span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">{products.length} items</span></div><div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500"><tr><th className="p-4">Product</th><th>Category</th><th>Price</th><th>Stock</th><th>Actions</th></tr></thead><tbody>{products.map(product => <tr key={product.id} className="border-t border-slate-100 transition hover:bg-slate-50"><td className="p-4"><div className="flex items-center gap-3"><img src={product.image_url} alt="" className="h-11 w-11 rounded-xl object-cover"/><div><p className="font-bold text-slate-800">{product.name}</p><p className="text-xs text-slate-400">ID #{product.id}</p></div></div></td><td><span className="rounded-full bg-indigo-50 px-2 py-1 text-xs font-semibold text-indigo-700">{product.category}</span></td><td className="font-semibold">{money(product.price)}</td><td><span className={product.stock < 10 ? 'font-bold text-amber-600' : 'font-semibold text-emerald-600'}>{product.stock}</span></td><td><button onClick={() => {setEditing(product.id); setForm({...product})}} className="mr-3 font-semibold text-indigo-600 hover:text-indigo-800">Edit</button><button onClick={() => removeProduct(product.id)} className="font-semibold text-red-500 hover:text-red-700">Delete</button></td></tr>)}</tbody></table></div></div>
      </section> : <section><div className="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div><h2 className="text-2xl font-bold">Order queue</h2><p className="mt-1 text-sm text-slate-500">Pending orders appear first, then the newest activity.</p></div><div className="flex flex-wrap gap-2"><select value={orderStatus} onChange={event => setOrderStatus(event.target.value)} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold outline-none"><option value="all">All statuses</option><option value="pending">Pending</option><option value="completed">Completed</option></select><select value={orderMonth} onChange={event => setOrderMonth(event.target.value)} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold outline-none"><option value="all">All months</option>{monthOptions.map(month => <option key={month} value={month}>{monthLabel(month)}</option>)}</select></div></div>{groupedOrders.length === 0 && <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-12 text-center"><div className="text-4xl">📦</div><h3 className="mt-4 text-xl font-bold">No orders found</h3><p className="mt-2 text-sm text-slate-500">New customer orders will appear here.</p></div>}{groupedOrders.map(group => <section key={group.key} className="mb-8"><div className="mb-3 flex items-center gap-3"><h3 className="text-lg font-bold text-slate-800">{monthLabel(group.key)}</h3><span className="rounded-full bg-slate-200 px-2.5 py-1 text-xs font-bold text-slate-600">{group.orders.length} order{group.orders.length === 1 ? '' : 's'}</span></div><div className="space-y-4">{group.orders.map(order => <article key={order.id} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md"><div className="flex flex-wrap items-start justify-between gap-4"><div className="flex items-start gap-3"><div className={order.status === 'completed' ? 'grid h-11 w-11 place-items-center rounded-2xl bg-emerald-100 text-emerald-700' : 'grid h-11 w-11 place-items-center rounded-2xl bg-amber-100 text-amber-700'}>{order.status === 'completed' ? '✓' : '!'}</div><div><div className="flex flex-wrap items-center gap-2"><h4 className="font-bold text-slate-900">Order #{order.id}</h4><StatusBadge status={order.status}/></div><p className="mt-1 text-sm font-semibold text-slate-700">{order.customer_name}</p><p className="mt-1 text-xs text-slate-400">{dateTime(order.created_at)} · {order.customer_email}</p></div></div><div className="text-left sm:text-right"><p className="text-2xl font-bold text-indigo-600">{money(order.total_amount)}</p><p className="mt-1 text-xs text-slate-400">{order.items.length} line item{order.items.length === 1 ? '' : 's'}</p></div></div><div className="mt-5 grid gap-4 border-t border-slate-100 pt-4 lg:grid-cols-[1fr_auto] lg:items-end"><div><p className="text-xs font-bold uppercase tracking-wider text-slate-400">Delivery</p><p className="mt-1 text-sm text-slate-600">{order.customer_address}</p><div className="mt-3 flex flex-wrap gap-2">{order.items.map(item => <span key={item.product_id} className="rounded-xl bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">{item.product_name} × {item.quantity}</span>)}</div></div><div className="flex flex-wrap gap-2 lg:justify-end"><button onClick={() => updateOrderStatus(order)} className={order.status === 'completed' ? 'rounded-xl border border-amber-200 px-3 py-2 text-sm font-bold text-amber-700 hover:bg-amber-50' : 'rounded-xl bg-emerald-600 px-3 py-2 text-sm font-bold text-white hover:bg-emerald-700'}>{order.status === 'completed' ? 'Mark pending' : 'Mark completed'}</button><button onClick={() => removeOrder(order)} className="rounded-xl border border-red-200 px-3 py-2 text-sm font-bold text-red-600 hover:bg-red-50">Delete order</button></div></div></article>)}</div></section>)}</section>}
    </main>
  </div>
}

createRoot(document.getElementById('root')).render(location.pathname.startsWith('/admin') ? <Admin/> : <Storefront/>)
