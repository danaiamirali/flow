require('dotenv').config();

const API_BASE_URL = process.env.API_BASE_URL;

if (!API_BASE_URL) {
    throw new Error("API_BASE_URL is not defined in the environment.");
}

export default API_BASE_URL;
