import React from "react";
import Head from "next/head";
import Link from "next/link";

export default function Landing() {
  return (
    <>
      <Head>
        <title>CABgrab - Login</title>
      </Head>
      <body className="landing-page">
        <div className="landing-container">
          <h1>
            Welcome to <span className="brand">CABgrab</span>
          </h1>
          <p className="tagline">
            Track Brown University course availability in real-time.
          </p>

          <a href="/api/login" className="login-btn">
            <img
              src="/static/logos/icons8-google-48.png"
              alt="Google"
              className="google-icon"
            />
            Sign in with Google
          </a>
        </div>
      </body>
    </>
  );
}