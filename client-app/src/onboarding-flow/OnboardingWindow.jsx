import React, { useEffect, useState } from "react";
import "./OnboardingWindow.css";

export default function OnboardingWindow({ onComplete }) {
  const [formData, setFormData] = useState({
    age: "",
    qualification: "",
    goals: "",
    challenges: "",
    description: "",
  });

  const [errors, setErrors] = useState({});
  const [learnerContext, setLearnerContext] = useState("");

  useEffect(() => {
    const saved = localStorage.getItem("onboardingData");
    if (saved) {
      setFormData(JSON.parse(saved));
    }
  }, []);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: "" }));
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.age) newErrors.age = "Age is required.";
    if (!formData.qualification) newErrors.qualification = "Select your qualification.";
    if (!formData.goals) newErrors.goals = "Please enter your learning goals.";
    if (!formData.challenges) newErrors.challenges = "Describe any challenges.";
    if (!formData.description) newErrors.description = "Tell us about yourself.";

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // const handleSubmit = async (e) => {
//     e.preventDefault();

//     // Basic validation
//     if (!formData.age || !formData.qualification || !formData.description) {
//       setError("Please fill out all required fields.");
//       return;
//     }

//     setError("");
//     setLoading(true);

//     try {
//       const res = await fetch("http://localhost:3001/api/onboarding", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify(formData),
//       });

//       if (!res.ok) {
//         throw new Error("Failed to submit onboarding data.");
//       }

//       const data = await res.json();
//       const context = data.learner_context || "No context returned.";

//       // Store locally
//       localStorage.setItem("onboardingData", JSON.stringify(formData));
//       localStorage.setItem("learnerContext", context);
//       setResponseContext(context);

//       // Optional: pass context back to app
//       if (onComplete) onComplete(context);
//     } catch (err) {
//       console.error(err);
//       setError("Submission failed. Please try again later.");
//     } finally {
//       setLoading(false);
//     }
//   };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    const context = `Learner Summary:
    - Age: ${formData.age}
    - Qualification: ${formData.qualification}
    - Goals: ${formData.goals}
    - Challenges: ${formData.challenges}
    - Description: ${formData.description}`;

    localStorage.setItem("onboardingData", JSON.stringify(formData));
    localStorage.setItem("learnerContext", context);
    setLearnerContext(context);

    if (onComplete) onComplete();
  };

  const handleReset = () => {
    setFormData({
      age: "",
      qualification: "",
      goals: "",
      challenges: "",
      description: "",
    });
    setErrors({});
    setLearnerContext("");
    localStorage.removeItem("onboardingData");
    localStorage.removeItem("learnerContext");
  };

  return (
    <div className="onboarding-container">
      <h1 className="onboarding-header">Tell Us About Yourself</h1>
      <form className="onboarding-form" onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-group">
            <label className="onboarding-label">Age</label>
            <input
              type="number"
              className="onboarding-input"
              placeholder="E.g., 25"
              value={formData.age}
              onChange={(e) => handleChange("age", e.target.value)}
            />
            {errors.age && <div className="error-message">{errors.age}</div>}
          </div>

          <div className="form-group">
            <label className="onboarding-label">Highest Educational Qualification</label>
            <select
              className="onboarding-select"
              value={formData.qualification}
              onChange={(e) => handleChange("qualification", e.target.value)}
            >
              <option value="">Select one...</option>
              <option value="High School">High School</option>
              <option value="Bachelor's">Bachelor's</option>
              <option value="Master's">Master's</option>
              <option value="PhD">PhD</option>
              <option value="Other">Other</option>
            </select>
            {errors.qualification && <div className="error-message">{errors.qualification}</div>}
          </div>

          <div className="form-group">
            <label className="onboarding-label">Learning Goals</label>
            <textarea
              className="onboarding-textarea"
              placeholder="E.g., I want to master machine learning and build real-world AI apps."
              value={formData.goals}
              onChange={(e) => handleChange("goals", e.target.value)}
            />
            {errors.goals && <div className="error-message">{errors.goals}</div>}
          </div>

          <div className="form-group">
            <label className="onboarding-label">Challenges Faced in Learning</label>
            <textarea
              className="onboarding-textarea"
              placeholder="E.g., I struggle with staying motivated and organizing study time."
              value={formData.challenges}
              onChange={(e) => handleChange("challenges", e.target.value)}
            />
            {errors.challenges && <div className="error-message">{errors.challenges}</div>}
          </div>
        </div>

        <div className="form-group">
          <label className="onboarding-label">Describe Yourself as a Learner</label>
          <textarea
            className="onboarding-textarea"
            placeholder="I am a graduate school student majoring in Computer Science and my research interests are LLMs, ML, AI, etc. I already studied these courses..."
            value={formData.description}
            onChange={(e) => handleChange("description", e.target.value)}
          />
          {errors.description && <div className="error-message">{errors.description}</div>}
        </div>

        <div className="button-row">
          <button type="submit" className="onboarding-button">Submit</button>
          <button type="button" className="onboarding-button secondary" onClick={handleReset}>
            Clear & Re-enter
          </button>
        </div>

        {learnerContext && (
          <div className="summary-preview">
            <strong>Saved Learner Context:</strong>
            <pre>{learnerContext}</pre>
          </div>
        )}
      </form>
    </div>
  );
}
