import React from "react";
import Head from "next/head";
import Link from "next/link";

export default function Landing() {
  return (
    <>
      <Head>
        <title>CABgrab - Login</title>
        {/* <link rel="stylesheet" href="/css/style.css" /> */}
      </Head>
      <body className="landing-page">
        <div className="landing-container">
          <h1>
            Welcome to <span className="brand">CABgrab</span>
          </h1>
          <p className="tagline">
            Track Brown University course availability in real-time.
          </p>

          {/* For now, link to login API directly */}
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