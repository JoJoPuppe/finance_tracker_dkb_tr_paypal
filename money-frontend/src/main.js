import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'

import axios from 'axios';

// Set the base URL for Axios to point to the backend API
axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5005';

createApp(App).mount('#app')
