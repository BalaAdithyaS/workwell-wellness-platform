function Header({ title }) {

  const name =
    localStorage.getItem("name");

  return (

    <div className="mb-8">

      <h1 className="text-5xl font-bold text-[#38240D]">
        {title}
      </h1>

      <p className="text-[#713600] mt-2">

        Welcome back, {name}

      </p>

    </div>

  );
}

export default Header;