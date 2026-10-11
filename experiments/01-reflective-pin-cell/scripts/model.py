"""Build the reflective UO2-water pin-cell model used in Lab 01."""

import openmc

FUEL_RADIUS = 0.39218  # cm
CLAD_RADIUS = 0.45720  # cm
PITCH = 1.26  # cm
HEIGHT = 1.0  # cm
TEMPERATURE = 293.6  # K


def make_materials():
    water = openmc.Material(material_id=1, name="water")
    water.add_nuclide("H1", 2.0, "ao")
    water.add_nuclide("O16", 1.0, "ao")
    water.set_density("g/cm3", 1.0)
    water.add_s_alpha_beta("c_H_in_H2O")

    fuel = openmc.Material(material_id=2, name="UO2 fuel")
    for nuclide, amount in {
        "U234": 4.4843e-6, "U235": 5.5815e-4,
        "U238": 2.2408e-2, "O16": 4.5829e-2,
    }.items():
        fuel.add_nuclide(nuclide, amount, "ao")
    fuel.set_density("g/cm3", 10.29769)

    cladding = openmc.Material(material_id=3, name="Zr cladding")
    for nuclide, amount in {
        "Zr90": 0.021827, "Zr91": 0.00476, "Zr92": 0.0072758,
        "Zr94": 0.0073734, "Zr96": 0.0011879,
    }.items():
        cladding.add_nuclide(nuclide, amount, "ao")
    cladding.set_density("g/cm3", 6.55)
    for material in [water, fuel, cladding]:
        material.temperature = TEMPERATURE
    return openmc.Materials([water, fuel, cladding])


def make_model(case, cross_sections=None):
    materials = make_materials()
    water, fuel, cladding = materials
    if cross_sections is not None:
        materials.cross_sections = str(cross_sections)

    fuel_surface = openmc.ZCylinder(surface_id=1, r=FUEL_RADIUS)
    clad_surface = openmc.ZCylinder(surface_id=2, r=CLAD_RADIUS)
    left = openmc.XPlane(surface_id=3, x0=-PITCH / 2, boundary_type="reflective")
    right = openmc.XPlane(surface_id=4, x0=PITCH / 2, boundary_type="reflective")
    bottom = openmc.YPlane(surface_id=5, y0=-PITCH / 2, boundary_type="reflective")
    top = openmc.YPlane(surface_id=6, y0=PITCH / 2, boundary_type="reflective")
    lower = openmc.ZPlane(surface_id=7, z0=-HEIGHT / 2, boundary_type="reflective")
    upper = openmc.ZPlane(surface_id=8, z0=HEIGHT / 2, boundary_type="reflective")
    axial = +lower & -upper
    square = +left & -right & +bottom & -top
    cells = [
        openmc.Cell(cell_id=1, name="fuel", fill=fuel,
                    region=-fuel_surface & axial),
        openmc.Cell(cell_id=2, name="cladding", fill=cladding,
                    region=+fuel_surface & -clad_surface & axial),
        openmc.Cell(cell_id=3, name="water", fill=water,
                    region=+clad_surface & square & axial),
    ]
    geometry = openmc.Geometry(openmc.Universe(universe_id=1, cells=cells))

    settings = openmc.Settings()
    settings.run_mode = "eigenvalue"
    settings.particles = case["particles"]
    settings.batches = case["batches"]
    settings.inactive = case["inactive"]
    settings.generations_per_batch = case["generations_per_batch"]
    settings.seed = case["seed"]
    if case["initial_source"] == "point":
        space = openmc.stats.Point((0.30, 0.0, 0.35))
    else:
        space = openmc.stats.Box(
            (-PITCH / 2, -PITCH / 2, -HEIGHT / 2),
            (PITCH / 2, PITCH / 2, HEIGHT / 2),
        )
    settings.source = openmc.IndependentSource(
        space=space,
        angle=openmc.stats.Isotropic(),
        energy=openmc.stats.Discrete([2.0e6], [1.0]),
        constraints={"fissionable": True},
    )
    if case["entropy_enabled"]:
        mesh = openmc.RegularMesh(mesh_id=1)
        mesh.lower_left = (-FUEL_RADIUS, -FUEL_RADIUS, -HEIGHT / 2)
        mesh.upper_right = (FUEL_RADIUS, FUEL_RADIUS, HEIGHT / 2)
        mesh.dimension = (4, 4, 4)
        settings.entropy_mesh = mesh
    return openmc.Model(geometry=geometry, materials=materials, settings=settings)
