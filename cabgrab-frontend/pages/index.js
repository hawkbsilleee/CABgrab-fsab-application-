import React, { useEffect, useState } from "react";
import Head from "next/head";

export default function Dashboard() {
  const [subscriptions, setSubscriptions] = useState([]);
  const [crn, setCrn] = useState("");

  // Fetch subscriptions from Flask
  useEffect(() => {
    fetch("api/subscriptions", {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => setSubscriptions(data))
      .catch((err) => console.error(err));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!/^[0-9, ]+$/.test(crn)) {
      alert("CRN must be numbers (you can separate multiple CRNs with commas)");
      return;
    }

    const res = await fetch("api/subscriptions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ crn }),
    });

    if (res.ok) {
      const newSub = await res.json();
      setSubscriptions([...subscriptions, newSub]);
      setCrn("");
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Stop tracking this course?")) return;

    await fetch(`api/subscriptions/${id}`, {
      method: "DELETE",
      credentials: "include",
    });

    setSubscriptions(subscriptions.filter((sub) => sub.id !== id));
  };

  return (
    <>
      <Head>
        <title>CABgrab - Dashboard</title>
        {/* <link rel="stylesheet" href="/css/style.css" /> */}
      </Head>
      <div className="container">
        <header>
          <h1>CABgrab</h1>
          <p className="subtitle">
            Track course availability and get notified when spots open up
          </p>
          <a href="api/logout" className="btn-secondary">
            Logout
          </a>
        </header>

        <main>
          <section className="form-section">
            <h2>Add Course to Track</h2>
            <form id="course-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="crn">Course CRN</label>
                <input
                  type="text"
                  id="crn"
                  name="crn"
                  placeholder="12345"
                  required
                  value={crn}
                  onChange={(e) => setCrn(e.target.value)}
                />
              </div>
              <button type="submit" className="btn-primary">
                Start Tracking
              </button>
            </form>
          </section>

          <section className="table-section">
            <h2>Your Tracked Courses</h2>
            {subscriptions.length > 0 ? (
              <div className="table-container">
                <table className="subscriptions-table">
                  <thead>
                    <tr>
                      <th>CRN</th>
                      <th>Date Added</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {subscriptions.map((sub) => (
                      <tr key={sub.id}>
                        <td>{sub.crn}</td>
                        <td>{sub.date_added || "N/A"}</td>
                        <td>
                          <button
                            onClick={() => handleDelete(sub.id)}
                            className="btn-delete"
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <p>
                  No courses being tracked yet. Add one above to get started!
                </p>
              </div>
            )}
          </section>
        </main>

        <footer>
          <p>by Ethan and Dhruv</p>
        </footer>
      </div>
    </>
  );
}